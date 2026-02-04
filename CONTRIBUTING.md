# Contribution guidelines

Contributing to this project should be as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features

## Github is used for everything

Github is used to host code, to track issues and feature requests, as well as accept pull requests.

Pull requests are the best way to propose changes to the codebase.

1. Fork the repo and create your branch from `main`.
2. If you've changed something, update the documentation.
3. Make sure your code passes all checks (see below).
4. Test your contribution.
5. Issue that pull request!

## Development Setup

### Using Dev Container (Recommended)

This project includes a dev container configuration for VS Code. Open the project in VS Code and use the "Reopen in Container" command for a pre-configured development environment.

### Manual Setup

Install dependencies using [uv](https://docs.astral.sh/uv/):

```bash
uv sync --dev
```

This installs all dependencies including dev tools (pytest, ruff, ty).

## Pre-Commit Checklist

**Before committing any changes, run ALL of these checks in order:**

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

Or run all checks in one command:

```bash
uv run pytest && uv run ruff format . && uv run ruff check . --fix && uv run ty check
```

**All checks must pass before committing.** CI will reject PRs that fail any of these.

## Testing Requirements

Run tests with coverage:

```bash
uv run pytest --cov=custom_components/komfovent
```

When fixing bugs:
1. Write a failing test case first that reproduces the bug
2. Verify the test fails as expected
3. Implement the fix
4. Verify the test now passes

## Code Quality Standards

This project uses:
- **[Ruff](https://docs.astral.sh/ruff/)** for linting and formatting (line length: 88, Python 3.13+)
- **[ty](https://github.com/astral-sh/ty)** for type checking

Use type hints for all function signatures.

## CI Workflows

The CI runs three workflow files on PRs:

1. **checks.yml** - Unit tests with pytest
2. **lint.yml** - Ruff check, Ruff format, ty type check
3. **validate.yml** - Hassfest and HACS validation

All must pass for PR approval.

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be under the same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using Github's [issues](../../issues)

GitHub issues are used to track public bugs.
Report a bug by [opening a new issue](../../issues/new/choose); it's that easy!

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

People *love* thorough bug reports. I'm not even kidding.

## License

By contributing, you agree that your contributions will be licensed under its MIT License.
