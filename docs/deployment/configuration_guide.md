# Configuration Guide

## Purpose
This document explains the enterprise configuration layers used to bootstrap the DikiliGeothermal SCADA platform across different physical environments.

## Scope
Defines the `ConfigManager` singleton, the `SystemConfig` schema, and how `APP_ENV` overrides work.

## Core Configuration Architecture
The platform utilizes a strictly validated `core/config/system_config.py` dataclass schema containing:
- `WorkspaceConfig`: Defines paths, layouts, and system bounds.
- `FeatureConfig`: Manages boolean toggles (e.g., `ai_enabled`, `simulation_mode`, `historian_enabled`).
- `DriverConfig`: Specifies the active hardware communication layer (OPC UA, Modbus TCP, MQTT).

## Environment Variables
The primary bootstrap mechanism is the `APP_ENV` environment variable, which dictates the active Deployment Profile:
- `APP_ENV=development`
- `APP_ENV=testing`
- `APP_ENV=simulation`
- `APP_ENV=pilot`
- `APP_ENV=production`

If an unknown `APP_ENV` is detected, the `ConfigManager` will purposefully raise a `ValueError` to prevent deploying untested logic to physical hardware.

## Modifying Configurations
Do not hardcode values into the business logic. All environment-specific overrides must be routed through `core/configuration.py`.

## Future Extensions
Integration with external Secrets Managers (e.g., AWS Secrets Manager, HashiCorp Vault) for securely injecting X.509 certificates into the `DriverConfig`.
