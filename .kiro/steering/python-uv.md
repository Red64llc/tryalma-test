# Python UV Package Management

Fast, reliable Python package management with [UV](https://docs.astral.sh/uv/) for single-package applications.

---

## Why UV

- **Speed**: 10-100x faster than pip/pip-tools
- **Deterministic**: Lock files ensure reproducible builds
- **Unified**: Replaces pip, pip-tools, virtualenv, pyenv in one tool
- **Compatible**: Works with existing `pyproject.toml` and PyPI

---

## Project Initialization

### New Project

```bash
# Create new project with src layout
uv init myproject --package

# Or initialize in current directory
uv init --package
```

### Existing Project

```bash
# Add uv.lock to existing pyproject.toml project
uv lock
```

### Generated Structure

```
myproject/
  src/
    myproject/
      __init__.py
  pyproject.toml
  .python-version
  uv.lock
  .venv/              # Created on first uv sync
```

---

## Python Version Management

### Pin Version (Both Files)

Always specify Python version in two places:

```toml
# pyproject.toml
[project]
requires-python = ">=3.12"
```

```
# .python-version
3.12
```

**Why both?**
- `requires-python`: Compatibility constraint for package consumers
- `.python-version`: Exact version for UV to install/use locally

### Install Python (If Needed)

```bash
# UV auto-installs if missing
uv sync

# Or explicitly install
uv python install 3.12
```

---

## Dependency Management

### Production Dependencies

```bash
# Add dependency
uv add httpx

# Add with version constraint
uv add "fastapi>=0.100"

# Add from git
uv add git+https://github.com/org/repo.git
```

### Development Dependencies

```bash
# Add to dev group
uv add --dev pytest pytest-cov ruff mypy

# Add to custom group
uv add --group docs mkdocs mkdocs-material
```

### pyproject.toml Structure

```toml
[project]
name = "myproject"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.100",
    "httpx>=0.25",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.0",
    "ruff>=0.4",
    "mypy>=1.10",
]
```

### Removing Dependencies

```bash
uv remove httpx
uv remove --dev pytest-mock
```

### Upgrading Dependencies

```bash
# Upgrade specific package
uv lock --upgrade-package httpx

# Upgrade all packages
uv lock --upgrade

# Then sync to apply
uv sync
```

---

## Virtual Environment

### Convention: Project-Local `.venv`

UV creates `.venv` in project root by default. Do not change this.

```bash
# Created automatically on first sync
uv sync

# Location
.venv/
```

### .gitignore

```gitignore
# Virtual environment
.venv/

# UV cache (optional, usually outside project)
.uv/
```

### Manual Creation (Rarely Needed)

```bash
# UV handles this automatically, but if needed:
uv venv
```

---

## Lock File Strategy

### Always Commit `uv.lock`

For applications, always commit the lock file:

```bash
git add uv.lock
git commit -m "Update dependencies"
```

**Why?**
- Reproducible builds across machines
- CI gets exact same versions
- Security: pinned hashes prevent supply chain attacks

### Lock vs Sync

```bash
# Update lock file (resolve dependencies)
uv lock

# Install from lock file (fast, exact versions)
uv sync

# Sync including dev dependencies (default)
uv sync

# Sync production only
uv sync --no-dev
```

---

## Running Commands

### Preferred: `uv run`

Always use `uv run` to execute commands. It auto-syncs dependencies.

```bash
# Run Python script
uv run python src/myproject/main.py

# Run module
uv run python -m myproject

# Run installed tool
uv run pytest
uv run ruff check src/

# Run with arguments
uv run pytest -v --cov=src
```

**Why `uv run`?**
- Auto-syncs if `uv.lock` changed
- No manual venv activation needed
- Works in CI without activation scripts

### One-Off Tools: `uvx`

For tools not in project dependencies:

```bash
# Run tool without installing
uvx ruff check .
uvx black --check src/

# Specific version
uvx ruff@0.4.0 check .
```

### Avoid Manual Activation

```bash
# Discouraged (works but unnecessary)
source .venv/bin/activate
pytest

# Preferred
uv run pytest
```

---

## Common Workflows

### Daily Development

```bash
# Start of day: ensure deps are synced
uv sync

# Run tests
uv run pytest

# Run linter
uv run ruff check src/

# Run type checker
uv run mypy src/

# Run application
uv run python -m myproject
```

### Adding a Feature with New Dependency

```bash
# Add dependency
uv add httpx

# Verify it works
uv run python -c "import httpx; print(httpx.__version__)"

# Commit both files
git add pyproject.toml uv.lock
git commit -m "Add httpx for HTTP client"
```

### CI Pipeline

```yaml
# GitHub Actions example
- name: Install UV
  uses: astral-sh/setup-uv@v4

- name: Install dependencies
  run: uv sync

- name: Run tests
  run: uv run pytest --cov=src

- name: Run linter
  run: uv run ruff check src/

- name: Run type checker
  run: uv run mypy src/
```

### Docker Build

```dockerfile
FROM python:3.12-slim

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first (layer caching)
COPY pyproject.toml uv.lock ./

# Install production dependencies only
RUN uv sync --no-dev --frozen

# Copy application code
COPY src/ ./src/

# Run application
CMD ["uv", "run", "python", "-m", "myproject"]
```

---

## Project Scripts

### Define in pyproject.toml

```toml
[project.scripts]
myproject = "myproject.cli:app"
```

### Run Script

```bash
# After uv sync, script is available
uv run myproject --help
```

For CLI patterns, see [python-cli.md](./python-cli.md).

---

## Integration with Testing

### Test Runner

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run specific test
uv run pytest tests/unit/test_core.py -v
```

For TDD patterns, see [python-tdd.md](./python-tdd.md).

### Watch Mode

```bash
# Install pytest-watch in dev
uv add --dev pytest-watch

# Run in watch mode
uv run ptw -- --lf -x
```

---

## Integration with FastAPI

### Development Server

```bash
# Run with auto-reload
uv run fastapi dev src/myproject/main.py

# Or with uvicorn directly
uv run uvicorn myproject.main:app --reload
```

For FastAPI patterns, see [python-fast-api.md](./python-fast-api.md).

---

## Command Reference

| Task | Command |
|------|---------|
| Initialize project | `uv init --package` |
| Add dependency | `uv add <package>` |
| Add dev dependency | `uv add --dev <package>` |
| Remove dependency | `uv remove <package>` |
| Update lock file | `uv lock` |
| Install dependencies | `uv sync` |
| Install production only | `uv sync --no-dev` |
| Upgrade package | `uv lock --upgrade-package <pkg>` |
| Upgrade all | `uv lock --upgrade` |
| Run command | `uv run <command>` |
| Run one-off tool | `uvx <tool>` |
| Show installed | `uv pip list` |
| Show outdated | `uv pip list --outdated` |

---

## Anti-Patterns to Avoid

### 1. Using pip Directly

```bash
# Bad: Bypasses lock file
pip install httpx

# Good: Uses UV's resolver
uv add httpx
```

### 2. Committing .venv

```bash
# Bad: .venv in git
git add .venv/

# Good: Only commit lock file
git add uv.lock
```

### 3. Manual Venv Activation in Scripts

```bash
# Bad: Fragile activation
source .venv/bin/activate && pytest

# Good: UV handles it
uv run pytest
```

### 4. Forgetting to Commit Lock File

```bash
# Bad: Only commit pyproject.toml
git add pyproject.toml

# Good: Commit both
git add pyproject.toml uv.lock
```

### 5. Using `--frozen` in Development

```bash
# Bad: Won't update if pyproject.toml changed
uv sync --frozen

# Good: Let UV sync naturally (use --frozen only in CI/Docker)
uv sync
```

---

_Focus on UV workflows and conventions. Tool-specific patterns belong in their respective steering files._
