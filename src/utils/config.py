"""
Application configuration for OneDrive Custom Backup Tool
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging


class AppConfig:
    """Application configuration manager"""

    def __init__(self, config_file: Optional[str] = None):
        self.logger = logging.getLogger(__name__)

        # Default config file location
        if not config_file:
            config_dir = Path.home() / ".onedrive-backup-tool"
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / "config.json"

        self.config_file = Path(config_file)
        self.config = self._load_default_config()
        self._load_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            "ui": {
                "theme": "dark",  # dark or light
                "window_size": "500x200",
                "remember_paths": True,
                "auto_detect_onedrive": True
            },
            "backup": {
                "verify_after_backup": True,
                "create_rollback_point": True,
                "timeout_seconds": 300,
                "min_free_space_mb": 100
            },
            "logging": {
                "level": "INFO",
                "max_file_size_mb": 10,
                "backup_count": 5,
                "console_output": True
            },
            "paths": {
                "last_source": "",
                "last_target": "",
                "onedrive_path": "",
                "temp_dir": ""
            },
            "advanced": {
                "check_admin_rights": True,
                "enable_cli": True,
                "auto_update_check": False
            }
        }

    def _load_config(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    self._merge_config(file_config)
                self.logger.info(
                    f"Configuration loaded from {self.config_file}")
            else:
                self.logger.info("Using default configuration")
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.logger.info("Using default configuration")

    def _merge_config(self, file_config: Dict[str, Any]):
        """Merge file config with default config"""
        for section, values in file_config.items():
            if section in self.config:
                if isinstance(values, dict):
                    self.config[section].update(values)
                else:
                    self.config[section] = values
            else:
                self.config[section] = values

    def save_config(self):
        """Save configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get configuration value

        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if not found

        Returns:
            Configuration value
        """
        try:
            return self.config.get(section, {}).get(key, default)
        except Exception:
            return default

    def set(self, section: str, key: str, value: Any):
        """
        Set configuration value

        Args:
            section: Configuration section
            key: Configuration key
            value: Value to set
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value

    def get_ui_theme(self) -> str:
        """Get UI theme setting"""
        return self.get("ui", "theme", "dark")

    def set_ui_theme(self, theme: str):
        """Set UI theme setting"""
        self.set("ui", "theme", theme)

    def get_window_size(self) -> str:
        """Get window size setting"""
        return self.get("ui", "window_size", "500x200")

    def get_remember_paths(self) -> bool:
        """Get remember paths setting"""
        return self.get("ui", "remember_paths", True)

    def get_last_source(self) -> str:
        """Get last source path"""
        return self.get("paths", "last_source", "")

    def set_last_source(self, path: str):
        """Set last source path"""
        self.set("paths", "last_source", path)

    def get_last_target(self) -> str:
        """Get last target path"""
        return self.get("paths", "last_target", "")

    def set_last_target(self, path: str):
        """Set last target path"""
        self.set("paths", "last_target", path)

    def get_onedrive_path(self) -> str:
        """Get OneDrive path"""
        return self.get("paths", "onedrive_path", "")

    def set_onedrive_path(self, path: str):
        """Set OneDrive path"""
        self.set("paths", "onedrive_path", path)

    def get_backup_timeout(self) -> int:
        """Get backup timeout in seconds"""
        return self.get("backup", "timeout_seconds", 300)

    def get_verify_after_backup(self) -> bool:
        """Get verify after backup setting"""
        return self.get("backup", "verify_after_backup", True)

    def get_logging_level(self) -> str:
        """Get logging level"""
        return self.get("logging", "level", "INFO")

    def is_admin_check_enabled(self) -> bool:
        """Check if admin rights check is enabled"""
        return self.get("advanced", "check_admin_rights", True)


# Global config instance
_config_instance = None


def get_config() -> AppConfig:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig()
    return _config_instance
