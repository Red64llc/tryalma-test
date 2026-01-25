# Python CLI Standards

Single-command CLI tools built with Typer, focusing on clean architecture, testability, and robust error handling.

---

## Framework: Typer

Use [Typer](https://typer.tiangolo.com/) for all CLI tools.

```python
import typer

app = typer.Typer()

@app.command()
def main(
    input_file: Path = typer.Argument(..., help="Input file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Process the input file."""
    ...

if __name__ == "__main__":
    app()
```

### Argument/Option Conventions

- **Arguments**: Required positional inputs (files, targets)
- **Options**: Optional flags with defaults (`--verbose`, `--output`)
- Always provide `help` text for all arguments and options
- Use type hints; Typer infers types and validation
- Prefer `Path` over `str` for file paths (automatic validation)

---

## Architecture Pattern

Separate CLI layer from business logic (Ports & Adapters).

```
src/
  cli.py          # Typer app, argument parsing, output formatting
  core.py         # Business logic (pure functions, no CLI dependencies)
  exceptions.py   # Custom exception hierarchy
```

### Why Separate?

- **Testability**: Test business logic without invoking CLI
- **Reusability**: Core logic can be called from other entry points
- **Single Responsibility**: CLI handles I/O; core handles logic

```python
# cli.py
from .core import process_data
from .exceptions import ValidationError

@app.command()
def main(input_file: Path) -> None:
    try:
        result = process_data(input_file)
        typer.echo(result)
    except ValidationError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
```

```python
# core.py (no typer imports)
def process_data(input_file: Path) -> str:
    """Pure business logic, easily testable."""
    ...
```

---

## Error Handling

### Exception Hierarchy

Define a custom exception base class; derive specific errors.

```python
# exceptions.py
class CLIError(Exception):
    """Base for all CLI errors."""
    exit_code: int = 1

class ValidationError(CLIError):
    """Invalid input or arguments."""
    exit_code = 2

class ProcessingError(CLIError):
    """Failure during processing."""
    exit_code = 3
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0    | Success |
| 1    | General error |
| 2    | Validation/input error |
| 3    | Processing error |

### Error Handling Pattern

Catch at CLI boundary; convert to user-friendly messages.

```python
@app.command()
def main(input_file: Path) -> None:
    try:
        result = process_data(input_file)
        typer.echo(result)
    except CLIError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=e.exit_code)
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(code=1)
```

### Principles

- Never expose stack traces to users (log internally if needed)
- Always exit with appropriate code
- Write errors to stderr (`err=True`)
- Provide actionable error messages

---

## Anti-Patterns to Avoid

### 1. Business Logic in CLI Layer

```python
# Bad: Logic mixed with CLI
@app.command()
def main(input_file: Path) -> None:
    data = input_file.read_text()
    processed = data.upper()  # Business logic here
    typer.echo(processed)

# Good: Delegate to core
@app.command()
def main(input_file: Path) -> None:
    result = process_data(input_file)
    typer.echo(result)
```

### 2. Catching Too Broadly

```python
# Bad: Swallows all errors silently
try:
    process()
except Exception:
    pass

# Good: Handle specific errors, re-raise or exit appropriately
try:
    process()
except ValidationError as e:
    typer.echo(f"Invalid input: {e}", err=True)
    raise typer.Exit(code=2)
```

### 3. Hardcoded Paths/Values

```python
# Bad
config_path = "/etc/myapp/config.yaml"

# Good: Use options with sensible defaults
config_path: Path = typer.Option(
    Path.home() / ".myapp" / "config.yaml",
    help="Path to configuration file"
)
```

### 4. Print Instead of Typer.echo

```python
# Bad: Bypasses Typer's output handling
print("Hello")

# Good: Uses Typer for consistent output
typer.echo("Hello")
```

---

## Best Practices Summary

1. **Separation of Concerns**: CLI parses and formats; core processes
2. **Type Hints**: Use throughout for clarity and Typer integration
3. **Custom Exceptions**: Structured hierarchy with exit codes
4. **User Experience**: Clear help text, actionable errors, proper exit codes
5. **No Side Effects in Imports**: Entry point guarded by `if __name__ == "__main__"`

For testing patterns, see [python-tdd.md](./python-tdd.md).

---

## Entry Point (Internal Distribution)

For internal tools, use `__main__.py` pattern:

```python
# src/__main__.py
from .cli import app

if __name__ == "__main__":
    app()
```

Run with: `python -m src` or create a shell alias.

---

_Focus on patterns and decisions. Implementation details belong in specs._
