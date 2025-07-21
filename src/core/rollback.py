"""
Rollback functionality for OneDrive Custom Backup Tool
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json
import tempfile


class RollbackManager:
    """Manages rollback functionality for backup operations"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rollback_data: Optional[Dict[str, Any]] = None
        self.temp_dir = Path(tempfile.gettempdir()) / "OneDriveBackupTool"
        self.temp_dir.mkdir(exist_ok=True)

    def create_rollback_point(self, source: str, target: str) -> bool:
        """
        Create a rollback point before backup operation

        Args:
            source: Source folder path
            target: Target OneDrive path

        Returns:
            True if rollback point created successfully
        """
        try:
            self.logger.info(
                f"Creating rollback point for: {source} -> {target}")

            source_path = Path(source)
            target_path = Path(target)

            # Store rollback information
            self.rollback_data = {
                "source": str(source_path.resolve()),
                "target": str(target_path.resolve()),
                "source_existed": source_path.exists(),
                "target_existed": target_path.exists(),
                "source_is_junction": self._is_junction(source_path),
                "backup_created": False,
                "junction_created": False,
                "timestamp": self._get_timestamp()
            }

            # If source is a junction, store its target
            if self.rollback_data["source_is_junction"]:
                self.rollback_data["original_junction_target"] = self._get_junction_target(
                    source_path)

            # Save rollback data to temp file
            rollback_file = self.temp_dir / "rollback.json"
            with open(rollback_file, 'w') as f:
                json.dump(self.rollback_data, f, indent=2)

            self.logger.info("Rollback point created successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create rollback point: {e}")
            return False

    def update_rollback_status(self, backup_created: bool = False, junction_created: bool = False):
        """Update rollback status during backup process"""
        if self.rollback_data:
            self.rollback_data["backup_created"] = backup_created
            self.rollback_data["junction_created"] = junction_created

            # Save updated data
            rollback_file = self.temp_dir / "rollback.json"
            try:
                with open(rollback_file, 'w') as f:
                    json.dump(self.rollback_data, f, indent=2)
            except Exception as e:
                self.logger.error(f"Failed to update rollback status: {e}")

    def rollback(self) -> bool:
        """
        Perform rollback operation

        Returns:
            True if rollback successful
        """
        try:
            if not self.rollback_data:
                # Try to load from temp file
                rollback_file = self.temp_dir / "rollback.json"
                if rollback_file.exists():
                    with open(rollback_file, 'r') as f:
                        self.rollback_data = json.load(f)
                else:
                    self.logger.warning("No rollback data available")
                    return False

            self.logger.info("Starting rollback operation")

            source_path = Path(self.rollback_data["source"])
            target_path = Path(self.rollback_data["target"])

            success = True

            # Step 1: Remove junction if it was created
            if self.rollback_data.get("junction_created", False):
                success &= self._remove_junction(source_path)

            # Step 2: Move back from target if backup was created
            if self.rollback_data.get("backup_created", False):
                success &= self._move_back_from_target(
                    source_path, target_path)

            # Step 3: Restore original junction if it existed
            if self.rollback_data.get("source_is_junction", False):
                original_target = self.rollback_data.get(
                    "original_junction_target")
                if original_target:
                    success &= self._restore_junction(
                        source_path, original_target)

            if success:
                self.logger.info("Rollback completed successfully")
            else:
                self.logger.error("Rollback completed with errors")

            return success

        except Exception as e:
            self.logger.error(f"Rollback operation failed: {e}")
            return False

    def clear_rollback_point(self):
        """Clear rollback point after successful backup"""
        try:
            self.rollback_data = None
            rollback_file = self.temp_dir / "rollback.json"
            if rollback_file.exists():
                rollback_file.unlink()
            self.logger.info("Rollback point cleared")
        except Exception as e:
            self.logger.error(f"Failed to clear rollback point: {e}")

    def _remove_junction(self, junction_path: Path) -> bool:
        """Remove junction link"""
        try:
            if junction_path.exists() and self._is_junction(junction_path):
                # Use rmdir for junction removal (safer than shutil.rmtree)
                import subprocess
                result = subprocess.run(
                    f'rmdir "{junction_path}"',
                    shell=True,
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    self.logger.info(f"Junction removed: {junction_path}")
                    return True
                else:
                    self.logger.error(
                        f"Failed to remove junction: {result.stderr}")
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Error removing junction: {e}")
            return False

    def _move_back_from_target(self, source_path: Path, target_path: Path) -> bool:
        """Move folder back from target to source"""
        try:
            if target_path.exists():
                # Ensure parent directory exists
                source_path.parent.mkdir(parents=True, exist_ok=True)

                # Move back using shutil
                shutil.move(str(target_path), str(source_path))
                self.logger.info(f"Moved back: {target_path} -> {source_path}")
                return True
            return True
        except Exception as e:
            self.logger.error(f"Error moving back from target: {e}")
            return False

    def _restore_junction(self, source_path: Path, target: str) -> bool:
        """Restore original junction"""
        try:
            import subprocess
            command = f'mklink /J "{source_path}" "{target}"'
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.logger.info(
                    f"Original junction restored: {source_path} -> {target}")
                return True
            else:
                self.logger.error(
                    f"Failed to restore junction: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Error restoring junction: {e}")
            return False

    def _is_junction(self, path: Path) -> bool:
        """Check if path is a junction point"""
        try:
            return path.is_dir() and path.is_symlink()
        except Exception:
            return False

    def _get_junction_target(self, path: Path) -> Optional[str]:
        """Get junction target path"""
        try:
            if self._is_junction(path):
                return str(path.readlink())
            return None
        except Exception:
            return None

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
