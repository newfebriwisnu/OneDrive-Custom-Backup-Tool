"""
Junction Link Manager for OneDrive Custom Backup Tool
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import subprocess

from core.powershell import PowerShellExecutor
from utils.paths import PathUtils


class JunctionManager:
    """Manages junction links - listing, removing, and maintaining them"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.powershell = PowerShellExecutor()
        self.path_utils = PathUtils()

    def list_junctions(self, search_paths: List[str] = None) -> List[Dict]:
        """
        List all junction links in specified paths or common locations

        Args:
            search_paths: List of paths to search for junctions

        Returns:
            List of dictionaries with junction information
        """
        try:
            if search_paths is None:
                # Default search paths
                search_paths = [
                    str(Path.home() / "Documents"),
                    str(Path.home() / "Desktop"),
                    str(Path.home() / "Downloads"),
                    str(Path.home() / "Pictures"),
                    str(Path.home() / "Videos"),
                    str(Path.home() / "Music"),
                    "C:\\Program Files",
                    "C:\\Program Files (x86)",
                    "C:\\Users",
                    "D:\\",
                ]

            junctions = []
            for search_path in search_paths:
                try:
                    if os.path.exists(search_path):
                        junctions.extend(
                            self._find_junctions_in_path(search_path))
                except Exception as e:
                    self.logger.warning(
                        f"Error searching in {search_path}: {e}")

            return junctions

        except Exception as e:
            self.logger.error(f"Error listing junctions: {e}")
            return []

    def _find_junctions_in_path(self, path: str, max_depth: int = 1) -> List[Dict]:
        """
        Find junction links in a specific path

        Args:
            path: Path to search
            max_depth: Maximum depth to search

        Returns:
            List of junction information dictionaries
        """
        junctions = []
        try:
            # Use PowerShell to find junctions efficiently
            # Ensure path ends with backslash for proper root directory handling
            if path.endswith(':'):
                search_path = path + '\\'
            elif not path.endswith('\\'):
                search_path = path + '\\'
            else:
                search_path = path

            ps_command = f"""Get-ChildItem -Path '{search_path}' -Recurse -Depth {max_depth} -Force -ErrorAction SilentlyContinue | Where-Object {{ $_.LinkType -eq 'Junction' }} | Select-Object FullName, Target, CreationTime | ConvertTo-Json -Depth 3"""

            success, output, error = self.powershell.run_command(ps_command)

            if success and output:
                import json
                try:
                    # Handle single object or array
                    data = json.loads(output)
                    if isinstance(data, dict):
                        data = [data]

                    for item in data:
                        target = item.get('Target', '')
                        # Handle both string and array formats
                        if isinstance(target, list):
                            target = target[0] if target else ''

                        junction_info = {
                            'source': item.get('FullName', ''),
                            'target': target,
                            'created': item.get('CreationTime', ''),
                            'type': 'Junction'
                        }
                        junctions.append(junction_info)

                except json.JSONDecodeError:
                    self.logger.warning(
                        f"Could not parse PowerShell output for {path}")

        except Exception as e:
            self.logger.error(f"Error finding junctions in {path}: {e}")

        return junctions

    def remove_junction(self, junction_path: str) -> Tuple[bool, str]:
        """
        Remove a junction link

        Args:
            junction_path: Path to the junction link

        Returns:
            Tuple of (success, message)
        """
        try:
            if not os.path.exists(junction_path):
                return False, "Junction path does not exist"

            if not self.path_utils.is_junction(junction_path):
                return False, "Path is not a junction link"

            # Remove the junction using PowerShell
            ps_command = f'Remove-Item -Path "{junction_path}" -Force'
            success, output, error = self.powershell.run_command(ps_command)

            if success:
                self.logger.info(
                    f"Successfully removed junction: {junction_path}")
                return True, f"Junction removed successfully: {junction_path}"
            else:
                self.logger.error(f"Failed to remove junction: {error}")
                return False, f"Failed to remove junction: {error}"

        except Exception as e:
            self.logger.error(f"Error removing junction {junction_path}: {e}")
            return False, f"Error removing junction: {str(e)}"

    def get_junction_info(self, path: str) -> Dict:
        """
        Get detailed information about a junction link

        Args:
            path: Path to check

        Returns:
            Dictionary with junction information
        """
        try:
            if not self.path_utils.is_junction(path):
                return {}

            # Get junction target using PowerShell
            ps_command = f'(Get-Item "{path}").Target'
            success, output, error = self.powershell.run_command(ps_command)

            if success and output:
                target = output.strip()
                return {
                    'source': path,
                    'target': target,
                    'exists': os.path.exists(path),
                    'target_exists': os.path.exists(target),
                    'type': 'Junction',
                    'created': os.path.getctime(path) if os.path.exists(path) else None
                }

        except Exception as e:
            self.logger.error(f"Error getting junction info for {path}: {e}")

        return {}

    def verify_junction(self, path: str) -> Tuple[bool, str]:
        """
        Verify if a junction link is working correctly

        Args:
            path: Path to verify

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            if not os.path.exists(path):
                return False, "Junction path does not exist"

            if not self.path_utils.is_junction(path):
                return False, "Path is not a junction link"

            # Get target path
            info = self.get_junction_info(path)
            if not info:
                return False, "Could not get junction information"

            target = info.get('target', '')
            if not target:
                return False, "Junction has no target"

            if not os.path.exists(target):
                return False, f"Junction target does not exist: {target}"

            return True, "Junction is valid and working"

        except Exception as e:
            self.logger.error(f"Error verifying junction {path}: {e}")
            return False, f"Error verifying junction: {str(e)}"
