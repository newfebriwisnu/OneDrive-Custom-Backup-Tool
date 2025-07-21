"""
Windows path utilities for OneDrive Custom Backup Tool
"""

import os
import sys
from pathlib import Path
from typing import Tuple, Optional
import subprocess
import logging

from core.powershell import PowerShellExecutor


class PathUtils:
    """Utility class for Windows path operations"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.powershell = PowerShellExecutor()

    def validate_source_path(self, path: str) -> Tuple[bool, str]:
        """
        Validate source path exists and is accessible

        Args:
            path: Source folder path

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not path or not path.strip():
                return False, "Source path cannot be empty"

            source_path = Path(path)

            # Check if path exists
            if not source_path.exists():
                return False, "Source path does not exist"

            # Check if it's a directory
            if not source_path.is_dir():
                return False, "Source path must be a directory"

            # Check read permissions
            if not os.access(source_path, os.R_OK):
                return False, "No read permission for source path"

            # Check if path is accessible
            try:
                list(source_path.iterdir())
            except PermissionError:
                return False, "Source path is not accessible (permission denied)"
            except Exception as e:
                return False, f"Source path is not accessible: {str(e)}"

            # Check path length (Windows limitation)
            if len(str(source_path.resolve())) > 260:
                return False, "Source path is too long (Windows path limit: 260 characters)"

            return True, ""

        except Exception as e:
            self.logger.error(f"Source path validation error: {e}")
            return False, f"Path validation error: {str(e)}"

    def validate_target_path(self, path: str) -> Tuple[bool, str]:
        """
        Validate target path is suitable for backup

        Args:
            path: Target OneDrive path

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not path or not path.strip():
                return False, "Target path cannot be empty"

            target_path = Path(path)

            # Check if target already exists
            if target_path.exists():
                if target_path.is_file():
                    return False, "Target path is a file, not a directory"
                # If it's a directory, check if it's empty or we can merge
                try:
                    # Check if directory is empty
                    if not any(target_path.iterdir()):
                        self.logger.info(
                            f"Target directory is empty: {target_path}")
                    else:
                        # Directory has contents, but we can still merge
                        self.logger.info(
                            f"Target directory exists with contents, will merge: {target_path}")
                except PermissionError:
                    return False, "Cannot access target directory to check contents"

            # Check if parent directory exists
            parent_dir = target_path.parent
            if not parent_dir.exists():
                return False, "Target parent directory does not exist"

            # Check write permissions on parent directory
            if not os.access(parent_dir, os.W_OK):
                return False, "No write permission for target parent directory"

            # Check available disk space (basic check)
            if not self._check_disk_space(parent_dir):
                return False, "Insufficient disk space at target location"

            # Check path length (Windows limitation)
            if len(str(target_path.resolve())) > 260:
                return False, "Target path is too long (Windows path limit: 260 characters)"

            # Check if target is in OneDrive folder (optional warning)
            if not self._is_onedrive_path(target_path):
                # This is a warning, not an error
                pass

            return True, ""

        except Exception as e:
            self.logger.error(f"Target path validation error: {e}")
            return False, f"Path validation error: {str(e)}"

    def is_junction(self, path: str) -> bool:
        """
        Check if path is a junction point using PowerShell

        Args:
            path: Path to check

        Returns:
            True if path is a junction point
        """
        try:
            if not path or not Path(path).exists():
                return False

            # Use PowerShell to check if it's a junction
            ps_command = f"Get-Item '{path}' | Where-Object {{$_.LinkType -eq 'Junction'}} | Select-Object -First 1"
            success, output, error = self.powershell.run_command(ps_command)

            if success and output.strip():
                return True
            return False

        except Exception as e:
            self.logger.error(
                f"Error checking junction status for {path}: {e}")
            return False

    def get_junction_target(self, path: str) -> Optional[str]:
        """
        Get junction target path using PowerShell

        Args:
            path: Junction path

        Returns:
            Target path if junction, None otherwise
        """
        try:
            if not self.is_junction(path):
                return None

            # Use PowerShell to get junction target
            ps_command = f"Get-Item '{path}' | Select-Object -ExpandProperty Target"
            success, output, error = self.powershell.run_command(ps_command)

            if success and output.strip():
                return output.strip()
            return None

        except Exception as e:
            self.logger.error(f"Error getting junction target for {path}: {e}")
            return None

    def get_onedrive_path(self) -> Optional[str]:
        """
        Auto-detect OneDrive folder path

        Returns:
            OneDrive folder path if found, None otherwise
        """
        try:
            # Check common OneDrive locations
            username = os.getenv('USERNAME')
            if not username:
                return None

            possible_paths = [
                f"C:\\Users\\{username}\\OneDrive",
                f"C:\\Users\\{username}\\OneDrive - Personal",
                f"C:\\Users\\{username}\\OneDrive - Business",
                f"C:\\Users\\{username}\\OneDrive for Business",
            ]

            for path_str in possible_paths:
                path = Path(path_str)
                if path.exists() and path.is_dir():
                    return str(path)

            # Try to detect from registry
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                     r"Software\\Microsoft\\OneDrive")
                onedrive_path = winreg.QueryValueEx(key, "UserFolder")[0]
                winreg.CloseKey(key)

                if Path(onedrive_path).exists():
                    return onedrive_path
            except Exception:
                pass

            return None

        except Exception as e:
            self.logger.error(f"Error detecting OneDrive path: {e}")
            return None

    def _is_onedrive_path(self, path: Path) -> bool:
        """Check if path is within OneDrive folder"""
        try:
            onedrive_path = self.get_onedrive_path()
            if not onedrive_path:
                return False

            onedrive_path_obj = Path(onedrive_path)
            try:
                path.resolve().relative_to(onedrive_path_obj.resolve())
                return True
            except ValueError:
                return False
        except Exception:
            return False

    def _check_disk_space(self, path: Path, min_space_mb: int = 100) -> bool:
        """
        Check available disk space

        Args:
            path: Path to check
            min_space_mb: Minimum required space in MB

        Returns:
            True if sufficient space available
        """
        try:
            if sys.platform == "win32":
                import ctypes

                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(str(path)),
                    ctypes.pointer(free_bytes),
                    None,
                    None
                )

                free_mb = free_bytes.value / (1024 * 1024)
                return free_mb >= min_space_mb
            else:
                # Fallback for non-Windows systems
                statvfs = os.statvfs(path)
                free_mb = (statvfs.f_frsize * statvfs.f_bavail) / (1024 * 1024)
                return free_mb >= min_space_mb

        except Exception as e:
            self.logger.error(f"Error checking disk space: {e}")
            return True  # Assume sufficient space if check fails

    def normalize_path(self, path: str) -> str:
        """
        Normalize Windows path

        Args:
            path: Path to normalize

        Returns:
            Normalized path
        """
        try:
            return str(Path(path).resolve())
        except Exception:
            return path

    def get_safe_filename(self, filename: str) -> str:
        """
        Get safe filename for Windows

        Args:
            filename: Original filename

        Returns:
            Safe filename
        """
        # Remove invalid characters for Windows
        invalid_chars = '<>:"/\\|?*'
        safe_name = filename

        for char in invalid_chars:
            safe_name = safe_name.replace(char, '_')

        # Remove trailing dots and spaces
        safe_name = safe_name.rstrip('. ')

        # Check for reserved names
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]

        if safe_name.upper() in reserved_names:
            safe_name = f"_{safe_name}"

        return safe_name
