"""
Core backup functionality for OneDrive Custom Backup Tool
"""

import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional, Callable

from core.powershell import PowerShellExecutor
from core.rollback import RollbackManager
from utils.paths import PathUtils


class BackupManager:
    """Manages the backup process using PowerShell commands"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.powershell = PowerShellExecutor()
        self.rollback_manager = RollbackManager()
        self.path_utils = PathUtils()

    def validate_paths(self, source: str, target: str) -> Tuple[bool, str]:
        """
        Validate source and target paths

        Args:
            source: Source folder path
            target: Target OneDrive path

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate source path
            source_valid, source_error = self.path_utils.validate_source_path(
                source)
            if not source_valid:
                return False, f"Source path error: {source_error}"

            # Validate target path
            target_valid, target_error = self.path_utils.validate_target_path(
                target)
            if not target_valid:
                return False, f"Target path error: {target_error}"

            # Check if source is already a junction
            if self.path_utils.is_junction(source):
                return False, "Source path is already a junction link"

            # Additional checks can be added here if needed
            # Target path existence is already handled in validate_target_path

            return True, ""

        except Exception as e:
            self.logger.error(f"Path validation error: {e}")
            return False, f"Validation error: {str(e)}"

    def execute_backup(self, source: str, target: str,
                       progress_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """
        Execute backup process: Move folder to OneDrive and create junction

        Args:
            source: Source folder path
            target: Target OneDrive path
            progress_callback: Optional callback for progress updates

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Starting backup: {source} -> {target}")

            # Step 1: Validate paths
            if progress_callback:
                progress_callback("Validating paths...", 10)

            is_valid, error_msg = self.validate_paths(source, target)
            if not is_valid:
                self.logger.error(f"Validation failed: {error_msg}")
                return False

            # Step 2: Prepare rollback point
            if progress_callback:
                progress_callback("Preparing rollback...", 20)

            # Calculate actual target path
            source_path = Path(source)
            target_path = Path(target)

            # If target is an existing directory, the actual target will be target/source_folder_name
            if target_path.exists() and target_path.is_dir():
                actual_target = target_path / source_path.name
                actual_target_str = str(actual_target)
                self.logger.info(
                    f"Target directory exists, actual target will be: {actual_target_str}")
            else:
                actual_target_str = target

            self.rollback_manager.create_rollback_point(
                source, actual_target_str)

            # Step 3: Move folder to OneDrive
            if progress_callback:
                progress_callback("Moving files to OneDrive...", 50)

            move_success = self._move_folder(source, target)
            if not move_success:
                self.logger.error("Failed to move folder to OneDrive")
                if progress_callback:
                    progress_callback("Move failed, rolling back...", 30)
                self.rollback_manager.rollback()
                return False

            # Step 4: Create junction link
            if progress_callback:
                progress_callback("Creating junction link...", 80)

            junction_success = self._create_junction(source, actual_target_str)
            if not junction_success:
                self.logger.error("Failed to create junction")
                self.rollback_manager.rollback()
                return False

            # Step 5: Verify result
            if progress_callback:
                progress_callback("Verifying backup...", 90)

            if not self._verify_backup(source, actual_target_str):
                self.logger.error("Backup verification failed")
                self.rollback_manager.rollback()
                return False

            if progress_callback:
                progress_callback("Backup completed successfully!", 100)

            self.logger.info("Backup completed successfully")
            self.rollback_manager.clear_rollback_point()
            return True

        except Exception as e:
            self.logger.error(f"Backup execution error: {e}")
            self.rollback_manager.rollback()
            return False

    def _move_folder(self, source: str, target: str) -> bool:
        """Move folder using PowerShell Move-Item command with better error handling"""
        try:
            self.logger.info(f"Attempting to move '{source}' to '{target}'")

            source_path = Path(source)
            target_path = Path(target)

            # If target is an existing directory, move source inside it
            if target_path.exists() and target_path.is_dir():
                # Create the final target path: target/source_folder_name
                final_target = target_path / source_path.name
                self.logger.info(
                    f"Target directory exists, moving to: {final_target}")
                target = str(final_target)
                target_path = final_target

            # Ensure target parent directory exists
            target_parent = target_path.parent
            if not target_parent.exists():
                self.logger.info(f"Creating parent directory: {target_parent}")
                target_parent.mkdir(parents=True, exist_ok=True)

            # Check if final target already exists
            if target_path.exists():
                self.logger.error(
                    f"Final target path already exists: {target_path}")
                return False

            # First try standard move
            command = f'Move-Item "{source}" "{target}" -Force'
            self.logger.info(f"Executing: {command}")
            success, stdout, stderr = self.powershell.run_command(command)

            if success:
                # Verify move was successful
                if not target_path.exists():
                    self.logger.error(
                        "Move operation completed but target doesn't exist")
                    return False

                if source_path.exists():
                    self.logger.error(
                        "Move operation completed but source still exists")
                    return False

                self.logger.info("Standard move completed successfully")
                return True

            # If standard move failed, try robocopy approach for better permission handling
            self.logger.warning(f"Standard move failed: {stderr}")
            self.logger.info(
                "Attempting robocopy method for better permission handling...")

            # Use robocopy to copy files, then remove source
            copy_command = f'robocopy "{source}" "{target}" /E /MOVE /R:3 /W:10 /MT:8'
            self.logger.info(f"Executing: {copy_command}")
            success, stdout, stderr = self.powershell.run_command(
                copy_command, timeout=120)

            # Robocopy returns various exit codes, 0-7 are success, 8+ are errors
            if success or "ERROR" not in stderr:
                # Check if target exists and source is gone
                if target_path.exists() and not source_path.exists():
                    self.logger.info("Robocopy move completed successfully")
                    return True
                elif target_path.exists() and source_path.exists():
                    # Files copied but source still exists, try to remove source
                    self.logger.info(
                        "Files copied, attempting to remove source...")
                    remove_command = f'Remove-Item "{source}" -Recurse -Force'
                    remove_success, _, remove_error = self.powershell.run_command(
                        remove_command)

                    if remove_success or not Path(source).exists():
                        return True
                    else:
                        self.logger.error(
                            f"Could not remove source after copy: {remove_error}")
                        return False

            self.logger.error(
                f"Both move methods failed. Last error: {stderr}")
            return False

        except Exception as e:
            self.logger.error(f"Move folder error: {e}")
            return False

    def _create_junction(self, source: str, target: str) -> bool:
        """Create junction link using PowerShell New-Item command"""
        try:
            # Execute PowerShell New-Item Junction command
            command = f'New-Item -ItemType Junction -Path "{source}" -Target "{target}"'
            success, stdout, stderr = self.powershell.run_command(command)

            if not success:
                self.logger.error(f"New-Item Junction failed: {stderr}")
                return False

            # Verify junction was created
            if not self.path_utils.is_junction(source):
                self.logger.error(
                    "Junction creation completed but junction doesn't exist")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Create junction error: {e}")
            return False

    def _verify_backup(self, source: str, target: str) -> bool:
        """Verify backup was created successfully"""
        try:
            self.logger.info(
                f"Verifying backup: source={source}, target={target}")

            # Check if source is now a junction
            if not self.path_utils.is_junction(source):
                self.logger.error(f"Source is not a junction: {source}")
                return False
            else:
                self.logger.info(f"SUCCESS: Source is a junction: {source}")

            # Check if target exists and is accessible
            if not Path(target).exists():
                self.logger.error(f"Target does not exist: {target}")
                return False
            else:
                self.logger.info(f"SUCCESS: Target exists: {target}")

            # Check if junction points to correct target
            junction_target = self.path_utils.get_junction_target(source)
            if not junction_target:
                self.logger.error(
                    f"Could not get junction target for: {source}")
                return False

            self.logger.info(f"Junction target: {junction_target}")
            self.logger.info(f"Expected target: {target}")

            # Compare resolved paths
            try:
                junction_resolved = Path(junction_target).resolve()
                target_resolved = Path(target).resolve()

                if junction_resolved != target_resolved:
                    self.logger.error(
                        f"Junction target mismatch: {junction_resolved} != {target_resolved}")
                    return False
                else:
                    self.logger.info(
                        f"SUCCESS: Junction points to correct target")

            except Exception as e:
                self.logger.error(f"Error resolving paths: {e}")
                return False

            self.logger.info("SUCCESS: Backup verification passed")
            return True

        except Exception as e:
            self.logger.error(f"Backup verification error: {e}")
            return False
