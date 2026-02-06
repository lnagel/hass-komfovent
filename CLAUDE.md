# CLAUDE.md - AI Agent Guidelines

This document provides essential guidelines for AI agents working on this codebase.

## Environment Setup

**ALWAYS run before any code quality checks:**

```bash
uv sync --dev
```

This installs all dependencies including dev tools (pytest, ruff, ty).

## Pre-Commit Checklist

**BEFORE committing any changes, run ALL of these checks in order:**

```bash
# 1. Run tests first - ensures code works correctly
uv run pytest

# 2. Format code with ruff (auto-fixes formatting issues)
uv run ruff format .

# 3. Lint with ruff (auto-fixes what it can)
uv run ruff check . --fix

# 4. Type check with ty
uv run ty check
```

**All checks must pass before committing.** CI will reject PRs that fail any of these.

## Pre-PR Checklist

**BEFORE creating a pull request, validate that your changes have 100% test coverage:**

```bash
# 1. Generate coverage XML report
uv run pytest --cov=custom_components/komfovent --cov-branch --cov-report=xml

# 2. Check diff coverage against main branch (100% required)
uv run diff-cover coverage.xml --compare-branch=main --fail-under=100
```

**If diff coverage fails:**
1. Review the output to see which specific lines lack coverage
2. Add tests for the uncovered lines
3. Re-run the diff coverage check until it passes

**Why this matters:** Codecov enforces diff coverage on PRs. Validating locally prevents wasted reviewer time on PRs that will fail CI.

## Project Structure

```
custom_components/komfovent/    # Main integration code
├── __init__.py                 # Integration setup and lifecycle
├── api.py                      # Modbus communication
├── binary_sensor.py            # Binary sensor entities
├── climate.py                  # Climate entity
├── config_flow.py              # UI configuration flow
├── const.py                    # Constants and configuration
├── coordinator.py              # Data update coordinator
├── diagnostics.py              # Diagnostics support
├── entity.py                   # Base entity classes
├── helpers.py                  # Utility functions
├── number.py                   # Number entities
├── select.py                   # Select entities
├── sensor.py                   # Sensor entities
├── services.py                 # Home Assistant services
├── switch.py                   # Switch entities
├── manifest.json               # Integration manifest
└── translations/               # UI translations

tests/                          # Test suite
├── conftest.py                 # Pytest fixtures
└── test_*.py                   # Unit tests

docs/                           # Documentation
├── MODBUS_C6.md                # C6 Modbus register documentation
└── MODBUS_C8.md                # C8 Modbus register documentation
```

## Documentation Synchronization

The `docs/MODBUS_C6.md` and `docs/MODBUS_C8.md` files document the Modbus register mappings for each controller type.

When making changes to entity mappings or register handling, ensure the documentation stays in sync.

## Testing Requirements

### Bug Fixes: Reproduce First

When fixing bugs:

1. **Write a failing test case first** that reproduces the bug
2. Verify the test fails as expected
3. Implement the fix
4. Verify the test now passes
5. Add any additional edge case tests

This ensures bugs don't regress and documents the expected behavior.

### New Features: Test Thoroughly

- Write tests for all new functionality
- Cover edge cases (null values, boundary conditions, error states)
- Test integration with Home Assistant entities where applicable

## Code Quality Standards

### Ruff Configuration

- Line length: 88 characters
- Target: Python 3.13+
- Select: ALL rules (with specific ignores, see pyproject.toml)
- Tests have relaxed rules for asserts, magic values, etc.

### Type Annotations

- Use type hints for all function signatures
- Use TypedDict for structured dictionaries
- Run `uv run ty check` to verify

### Constants

- Extract magic numbers to `const.py`
- Document units in comments (seconds, percentages, ratios)

## Git Commit Practices

### Good Commit History

- **Each meaningful change deserves its own commit**
- Prefer new incremental commits over amending
- Write clear, descriptive commit messages
- Use conventional format: `Fix X`, `Add Y`, `Update Z`
- PRs are squash-merged, so we can have detailed commit history during development

### When to Amend

Only amend commits for:

- Re-running linter/formatter (formatting fixes)
- Fixing typos in the same logical change
- Never amend commits that are already pushed

### When NOT to Amend

- Meaningful code changes should always be new commits
- Bug fixes that change behavior
- New features or refactors

## Common Pitfalls to Avoid

### 1. Forgetting `uv sync`

```bash
# WRONG - tools not installed
uv run pytest  # Error: pytest not found

# RIGHT
uv sync --dev
uv run pytest
```

### 2. Committing Without Full Check Cycle

```bash
# WRONG - only ran tests
uv run pytest
git commit

# RIGHT - full verification
uv run pytest && uv run ruff format . && uv run ruff check . --fix && uv run ty check
git commit
```

### 3. Fixing Bugs Without Tests

```python
# WRONG - Just fix the code
def some_function(...):
    return fixed_value  # "trust me it works now"


# RIGHT - Write failing test first
def test_some_function_edge_case():
    # This test should fail before the fix
    assert some_function(edge_case) == expected
```

## CI Workflows

The CI runs three workflow files on PRs:

1. **checks.yml** - Unit tests with pytest
2. **lint.yml** - Ruff check, Ruff format, ty type check
3. **validate.yml** - Hassfest and HACS validation

All must pass for PR approval.

## Quick Reference Commands

```bash
# Setup environment
uv sync --dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=custom_components/komfovent --cov-branch

# Format code
uv run ruff format .

# Lint and auto-fix
uv run ruff check . --fix

# Type check
uv run ty check

# Full pre-commit check
uv run pytest && uv run ruff format . && uv run ruff check . --fix && uv run ty check

# Check diff coverage (before creating PR)
uv run pytest --cov=custom_components/komfovent --cov-branch --cov-report=xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=100

# Bump version (updates pyproject.toml and manifest.json)
uv run bump-my-version bump patch  # 0.7.4 -> 0.7.5
uv run bump-my-version bump minor  # 0.7.4 -> 0.8.0
uv run bump-my-version bump major  # 0.7.4 -> 1.0.0
```

## Modbus Communication

This integration communicates with Komfovent devices via Modbus TCP. Key points:

- Uses pymodbus library for Modbus communication
- Supports C6, C6M, and C8 controller types
- Register mappings differ between controller types
- See `docs/MODBUS_C6.md` and `docs/MODBUS_C8.md` for register documentation
