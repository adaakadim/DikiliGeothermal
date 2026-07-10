# Security Policy

## Supported Versions

Security updates are only applied to the latest `MAJOR.MINOR` version.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

Because this SCADA system interacts with high-voltage and high-pressure industrial equipment, security vulnerabilities are treated as `CRITICAL` severity events.

If you discover a potential vulnerability (e.g., an unauthenticated API endpoint, a buffer overflow in a driver, or a privilege escalation flaw in the RBAC), **do not open a public issue.**

Please securely email the repository maintainers immediately. We will coordinate a patched release and issue a formal CVE before public disclosure.
