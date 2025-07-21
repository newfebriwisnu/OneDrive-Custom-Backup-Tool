"""
Real-time input validation for OneDrive Custom Backup Tool
"""

import tkinter as tk
from tkinter import ttk
import logging
import os
from typing import Optional, Callable
from pathlib import Path
import threading
import time

from utils.paths import PathUtils


class PathValidator:
    """Handles real-time path validation with visual feedback"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.path_utils = PathUtils()
        self.validation_cache = {}
        self.validation_timers = {}

    def validate_source_realtime(self, widget, path: str) -> bool:
        """
        Validate source path with real-time feedback

        Args:
            widget: Entry widget to provide feedback
            path: Path to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Cancel previous timer if exists
            widget_id = str(widget)
            if widget_id in self.validation_timers:
                self.validation_timers[widget_id].cancel()

            # Schedule validation with delay to avoid excessive calls
            timer = threading.Timer(
                0.5, self._validate_source_delayed, args=(widget, path))
            self.validation_timers[widget_id] = timer
            timer.start()

            return True  # Return True for now, actual validation is delayed

        except Exception as e:
            self.logger.error(f"Error in real-time source validation: {e}")
            self._set_validation_style(widget, 'error')
            return False

    def validate_target_realtime(self, widget, path: str) -> bool:
        """
        Validate target path with real-time feedback

        Args:
            widget: Entry widget to provide feedback
            path: Path to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Cancel previous timer if exists
            widget_id = str(widget)
            if widget_id in self.validation_timers:
                self.validation_timers[widget_id].cancel()

            # Schedule validation with delay to avoid excessive calls
            timer = threading.Timer(
                0.5, self._validate_target_delayed, args=(widget, path))
            self.validation_timers[widget_id] = timer
            timer.start()

            return True  # Return True for now, actual validation is delayed

        except Exception as e:
            self.logger.error(f"Error in real-time target validation: {e}")
            self._set_validation_style(widget, 'error')
            return False

    def _validate_source_delayed(self, widget, path: str):
        """Delayed source validation"""
        try:
            if not path.strip():
                self._set_validation_style(widget, 'normal')
                return

            # Check cache first
            cache_key = f"source:{path}"
            if cache_key in self.validation_cache:
                cached_result = self.validation_cache[cache_key]
                # 5 second cache
                if time.time() - cached_result['timestamp'] < 5:
                    self._set_validation_style(widget,
                                               'success' if cached_result['valid'] else 'error')
                    return

            # Perform validation
            is_valid, error_msg = self.path_utils.validate_source_path(path)

            # Cache result
            self.validation_cache[cache_key] = {
                'valid': is_valid,
                'error': error_msg,
                'timestamp': time.time()
            }

            # Update UI on main thread
            widget.after(0, self._set_validation_style, widget,
                         'success' if is_valid else 'error')

            if not is_valid:
                self.logger.debug(f"Source validation failed: {error_msg}")

        except Exception as e:
            self.logger.error(f"Error in delayed source validation: {e}")
            widget.after(0, self._set_validation_style, widget, 'error')

    def _validate_target_delayed(self, widget, path: str):
        """Delayed target validation"""
        try:
            if not path.strip():
                self._set_validation_style(widget, 'normal')
                return

            # Check cache first
            cache_key = f"target:{path}"
            if cache_key in self.validation_cache:
                cached_result = self.validation_cache[cache_key]
                # 5 second cache
                if time.time() - cached_result['timestamp'] < 5:
                    self._set_validation_style(widget,
                                               'success' if cached_result['valid'] else 'error')
                    return

            # Perform validation
            is_valid, error_msg = self.path_utils.validate_target_path(path)

            # Special handling for OneDrive path suggestion
            if is_valid and not self.path_utils._is_onedrive_path(Path(path)):
                # Show warning style for non-OneDrive paths
                self._set_validation_style(widget, 'warning')
                is_valid = True  # Still valid, just not in OneDrive
            else:
                # Cache result
                self.validation_cache[cache_key] = {
                    'valid': is_valid,
                    'error': error_msg,
                    'timestamp': time.time()
                }

                # Update UI on main thread
                widget.after(0, self._set_validation_style, widget,
                             'success' if is_valid else 'error')

            if not is_valid:
                self.logger.debug(f"Target validation failed: {error_msg}")

        except Exception as e:
            self.logger.error(f"Error in delayed target validation: {e}")
            widget.after(0, self._set_validation_style, widget, 'error')

    def _set_validation_style(self, widget, style: str):
        """Set validation style on widget"""
        try:
            # Simple styling for basic tk.Entry widgets
            if style == 'success':
                widget.configure(bg='#404040', fg='#00ff00',
                                 relief='solid', bd=1)
            elif style == 'error':
                widget.configure(bg='#404040', fg='#ff4444',
                                 relief='solid', bd=1)
            elif style == 'warning':
                widget.configure(bg='#404040', fg='#ffff00',
                                 relief='solid', bd=1)
            else:
                widget.configure(bg='#404040', fg='#ffffff',
                                 relief='flat', bd=2)

        except Exception as e:
            self.logger.error(f"Error setting validation style: {e}")

    def validate_immediately(self, path: str, path_type: str = 'source') -> tuple:
        """
        Immediate validation without UI feedback

        Args:
            path: Path to validate
            path_type: Type of path ('source' or 'target')

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if path_type == 'source':
                return self.path_utils.validate_source_path(path)
            else:
                return self.path_utils.validate_target_path(path)
        except Exception as e:
            self.logger.error(f"Error in immediate validation: {e}")
            return False, f"Validation error: {str(e)}"

    def clear_cache(self):
        """Clear validation cache"""
        try:
            self.validation_cache.clear()
            self.logger.debug("Validation cache cleared")
        except Exception as e:
            self.logger.error(f"Error clearing validation cache: {e}")

    def cleanup(self):
        """Cleanup resources"""
        try:
            # Cancel all pending timers
            for timer in self.validation_timers.values():
                timer.cancel()
            self.validation_timers.clear()

            # Clear cache
            self.clear_cache()

            self.logger.debug("PathValidator cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def get_validation_message(self, path: str, path_type: str = 'source') -> str:
        """
        Get validation message for path

        Args:
            path: Path to validate
            path_type: Type of path ('source' or 'target')

        Returns:
            Validation message
        """
        try:
            is_valid, error_msg = self.validate_immediately(path, path_type)

            if is_valid:
                return "Path is valid"
            else:
                return error_msg

        except Exception as e:
            return f"Validation error: {str(e)}"

    def suggest_onedrive_path(self, source_path: str) -> str:
        """
        Suggest OneDrive target path based on source path

        Args:
            source_path: Source folder path

        Returns:
            Suggested OneDrive target path
        """
        try:
            onedrive_path = self.path_utils.get_onedrive_path()
            if not onedrive_path:
                return ""

            # Get folder name from source path
            source_name = Path(source_path).name

            # Create suggested path
            suggested_path = Path(onedrive_path) / "Backup" / source_name

            return str(suggested_path)

        except Exception as e:
            self.logger.error(f"Error suggesting OneDrive path: {e}")
            return ""

    def is_path_available(self, path: str) -> bool:
        """
        Quick check if path is available (doesn't exist)

        Args:
            path: Path to check

        Returns:
            True if path is available (doesn't exist)
        """
        try:
            return not Path(path).exists()
        except Exception:
            return False

    def get_path_info(self, path: str) -> dict:
        """
        Get detailed path information

        Args:
            path: Path to analyze

        Returns:
            Dictionary with path information
        """
        try:
            path_obj = Path(path)

            info = {
                'exists': path_obj.exists(),
                'is_dir': path_obj.is_dir() if path_obj.exists() else False,
                'is_file': path_obj.is_file() if path_obj.exists() else False,
                'is_junction': self.path_utils.is_junction(path),
                'is_onedrive': self.path_utils._is_onedrive_path(path_obj) if path_obj.exists() else False,
                'parent_exists': path_obj.parent.exists(),
                'readable': path_obj.exists() and os.access(path_obj, os.R_OK),
                'writable': path_obj.parent.exists() and os.access(path_obj.parent, os.W_OK),
                'size': path_obj.stat().st_size if path_obj.exists() else 0,
                'absolute_path': str(path_obj.resolve())
            }

            if info['is_junction']:
                info['junction_target'] = self.path_utils.get_junction_target(
                    path)

            return info

        except Exception as e:
            self.logger.error(f"Error getting path info: {e}")
            return {
                'exists': False,
                'error': str(e)
            }
