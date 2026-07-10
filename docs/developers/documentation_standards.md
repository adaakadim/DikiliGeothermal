# Documentation Standards

This document defines the strict enterprise templates required for all documentation written for the DikiliGeothermal platform.

## Standard Markdown Template
All architectural and module documentation MUST follow this template:

```markdown
# Module Name

## Purpose
A single paragraph explaining what this module does.

## Scope
Defines the boundaries of the module (what it handles vs. what is delegated).

## Inputs & Outputs
- **Inputs:** Expected data sources, configuration injections, or API triggers.
- **Outputs:** Data pushed, files written, or external APIs called.

## Dependencies
List of internal SCADA modules or external Python packages required.

## Usage Example
A brief code snippet demonstrating how to instantiate or interact with the module.

## Future Extensions
Notes for open-source maintainers on planned upgrades or architectural limits.
```

## Naming Conventions
- All files must be `lowercase_with_underscores.md`.
- No spaces in filenames.
- Use explicit cross-linking between documents using relative paths.

## Python Coding Standards
To maintain enterprise reliability, all Python contributions must adhere to:

1. **Type Hints:** Every function parameter and return type MUST be explicitly type-hinted.
2. **Docstrings:** Use Google-style docstrings for all classes and public methods.
3. **Error Handling:** Never swallow exceptions blindly (`except Exception: pass`). Always catch specific exceptions (e.g., `ConnectionError`) and log them via the central `AuditLogger`.
4. **Logging:** Do not use `print()`. Use the structured python `logging` module or the internal `AuditLogger` for security events.
5. **Testing:** All new logic MUST be accompanied by a corresponding `test_*.py` file in the `tests/` directory.
