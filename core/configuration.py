import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any

# We setup a basic logger for the configuration loader itself.
# It will be overridden by the enterprise logger later.
logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Centralized Configuration Loader.
    Loads default.yaml and merges environment-specific overrides (e.g. development.yaml).
    """
    _instance = None
    VALID_PROFILES = ["development", "testing", "simulation", "pilot", "production"]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._config = {}
            cls._instance._env = os.environ.get("APP_ENV", "development").lower()
            if cls._instance._env not in cls.VALID_PROFILES:
                logger.critical(f"Invalid APP_ENV '{cls._instance._env}'. Must be one of {cls.VALID_PROFILES}")
                raise ValueError(f"Invalid deployment profile: {cls._instance._env}")
            cls._instance._load_config()
            cls._instance.validate_deployment()
        return cls._instance

    def _load_config(self):
        """Loads default.yaml, {APP_ENV}.yaml, and user_state.yaml."""
        config_dir = Path("config")
        
        # Ensure config directory exists
        if not config_dir.exists():
            logger.warning(f"Config directory '{config_dir}' not found. Using empty defaults.")
            return

        # Load default
        default_path = config_dir / "default.yaml"
        if default_path.exists():
            try:
                with open(default_path, "r", encoding="utf-8") as f:
                    self._config = yaml.safe_load(f) or {}
                logger.debug(f"Loaded {default_path}")
            except Exception as e:
                logger.error(f"Failed to load {default_path}: {e}")
        
        # Load environment specific
        env_path = config_dir / f"{self._env}.yaml"
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    env_config = yaml.safe_load(f) or {}
                self._merge(self._config, env_config)
                logger.debug(f"Loaded {env_path}")
            except Exception as e:
                logger.error(f"Failed to load {env_path}: {e}")
        else:
            logger.warning(f"Environment config '{env_path}' not found. Relying on default.")
            
        # Load user state
        user_path = config_dir / "user_state.yaml"
        if user_path.exists():
            try:
                with open(user_path, "r", encoding="utf-8") as f:
                    user_config = yaml.safe_load(f) or {}
                self._merge(self._config, user_config)
                logger.debug(f"Loaded {user_path}")
            except Exception as e:
                logger.error(f"Failed to load {user_path}: {e}")

    def _merge(self, base: dict, override: dict):
        """Deep merge two dictionaries."""
        for k, v in override.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                self._merge(base[k], v)
            else:
                base[k] = v

    @property
    def environment(self) -> str:
        return self._env

    def validate_deployment(self):
        """Validates that the required directories and feature configurations are valid."""
        # 1. Validate required paths based on enabled features
        if self.get("features.historian", True):
            db_path = Path(self.get("app.db_path", "data/historian.db"))
            if not db_path.parent.exists():
                try:
                    db_path.parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    logger.critical(f"Historian directory '{db_path.parent}' is not writable: {e}")
                    raise RuntimeError("Historian path is not writable.")
        
        # 2. Conflicting feature validation
        if self._env == "production" and self.get("features.simulation_engine", False):
            logger.critical("Configuration Conflict: Cannot run Simulation Engine in Production profile.")
            raise ValueError("Simulation Engine cannot be enabled in Production.")
            
        if self._env == "simulation" and self.get("features.modbus_driver", False):
            logger.critical("Configuration Conflict: Cannot run Modbus driver in Simulation profile.")
            raise ValueError("Modbus driver cannot be enabled in Simulation.")
            
        logger.info(f"Deployment profile '{self._env}' validated successfully.")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot-notation.
        Example: config.get("app.name")
        """
        keys = key.split(".")
        val = self._config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    def set(self, key: str, value: Any):
        """
        Set a configuration value using dot-notation.
        Example: config.set("ui.layers.sensor", False)
        """
        keys = key.split(".")
        d = self._config
        for k in keys[:-1]:
            if k not in d or not isinstance(d[k], dict):
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value
        
    def save(self):
        """Saves current state to user_state.yaml"""
        config_dir = Path("config")
        if not config_dir.exists():
            config_dir.mkdir(parents=True, exist_ok=True)
            
        user_path = config_dir / "user_state.yaml"
        try:
            # We don't want to save the entire config, just what changed, but since we merge it all into self._config,
            # saving self._config is fine. Alternatively, we could save only specific keys. 
            # To keep it simple, we'll save the whole config for now.
            with open(user_path, "w", encoding="utf-8") as f:
                yaml.dump(self._config, f, default_flow_style=False)
            logger.debug(f"Saved config to {user_path}")
        except Exception as e:
            logger.error(f"Failed to save {user_path}: {e}")

# Global instance for easy import
config = ConfigManager()
