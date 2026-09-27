# Contribution guidelines

Contributing to this project should be as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features

## GitHub is used for everything

GitHub is used to host code, to track bugs in issues, to discuss feature requests in discussions, as well as accept pull requests.

Pull requests are the best way to propose changes to the codebase, but please read [Scope of contributions](#scope-of-contributions) first.

1. For anything beyond a small, focused fix, start a thread in [GitHub Discussions](../../discussions) and agree on the approach with the maintainer.
2. Fork the repo and create your branch from `main`.
3. If you've changed something, update the documentation.
4. Make sure your code passes all checks (see below).
5. Test your contribution.
6. Issue that pull request, linking the related issue or discussion.

## Development setup

### Using Dev Container (Recommended)

This project includes a dev container configuration for VS Code. Open the project in VS Code and use the "Reopen in Container" command for a pre-configured development environment.

### Manual setup

Install dependencies using [uv](https://docs.astral.sh/uv/):

```bash
uv sync --dev
```

This installs all dependencies including dev tools (pytest, ruff, ty).

## Pre-commit checklist

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

## Testing

New contributions must not lower test coverage. New and changed code should come with tests that exercise it. CI reports coverage on every pull request and fails if it drops below what the project requires; the exact thresholds are configured per project in `pyproject.toml` and `codecov.yaml`.

When fixing bugs:

1. Write a failing test case first that reproduces the bug
2. Verify the test fails as expected
3. Implement the fix
4. Verify the test now passes

To check coverage locally, including which of your changed lines are not covered:

```bash
uv run pytest --cov --cov-branch --cov-report=term --cov-report=xml
uv run diff-cover coverage.xml --compare-branch=main
```

## Code quality standards

This project uses:

- **[Ruff](https://docs.astral.sh/ruff/)** for linting and formatting (line length: 88, Python 3.14+)
- **[ty](https://github.com/astral-sh/ty)** for type checking

Use type hints for all function signatures.

## CI workflows

The CI runs three workflow files on PRs:

1. **checks.yml** - Unit tests with pytest and coverage
2. **lint.yml** - Ruff check, Ruff format, ty type check
3. **validate.yml** - Hassfest and HACS validation

All must pass for PR approval.

## Scope of contributions

Small, focused fixes are welcome as pull requests directly. For anything larger:

- **Discuss refactoring and behavior changes first.** Pull requests that refactor code or change behavior without prior agreement are unlikely to be merged. If a fix needs refactoring, start a thread in [GitHub Discussions](../../discussions) and agree on the approach with the maintainer before writing code.
- **Automated contributions.** Pull requests created by bots or AI agents without a prior discussion may be closed without review. Writing the code is rarely the hard part; deciding whether and how a change should be made is.

AI tools are fine to use, and the maintainer uses them too, but you are responsible for what you submit. Review and understand every change, and be able to explain it in your own words. This follows the principles of the [Open Home Foundation AI Policy](https://developers.home-assistant.io/docs/ai_policy/).

Bug reports must come from a real installation: logs, diagnostics and reproduction steps must be what you actually observed, not generated.

## Report bugs using GitHub's [issues](../../issues)

GitHub issues are used to track public bugs.
Report a bug by [opening a new issue](../../issues/new/choose) using the **Bug report** template.

**Bug reports must follow the template.** Fill in every required field, including System Health details, reproduction steps and debug logs, and attach diagnostics where possible. Bug reports that do not follow the template may be closed.

Beyond the template, **great bug reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

People *love* thorough bug reports. I'm not even kidding.

## Request features using GitHub's [discussions](../../discussions)

Feature requests and ideas are preferably discussed in GitHub Discussions.
Start a [new discussion](../../discussions/new/choose) describing the problem you are trying to solve, not only the solution you have in mind.
Feature requests opened as issues may be converted into a discussion.
If the maintainer agrees on the approach, it can then be implemented in a pull request.

## License

By contributing, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
