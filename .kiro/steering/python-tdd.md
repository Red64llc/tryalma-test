# Python Test-Driven Development

Test-first development with pytest, focusing on fast unit tests, contract testing, and minimal mocking.

---

## TDD Philosophy

### Red-Green-Refactor Cycle

1. **Red**: Write a failing test that defines expected behavior
2. **Green**: Write minimal code to make the test pass
3. **Refactor**: Improve design while keeping tests green

```python
# 1. RED - Start with the test
def test_parse_config_extracts_name():
    config = {"name": "myapp", "version": "1.0"}

    result = parse_config(config)

    assert result.name == "myapp"

# 2. GREEN - Minimal implementation
@dataclass
class Config:
    name: str

def parse_config(config: dict) -> Config:
    return Config(name=config["name"])

# 3. REFACTOR - Improve (add validation, typing, etc.)
```

### Test-First Design Patterns

**Write the test first to discover the API:**

```python
# Before writing any implementation, write how you WANT to use it
def test_validator_rejects_empty_email():
    validator = EmailValidator()

    result = validator.validate("")

    assert result.is_valid is False
    assert "empty" in result.error.lower()
```

This approach:
- Forces clear interfaces before implementation
- Documents expected behavior
- Prevents over-engineering

**Design principle**: If a test is hard to write, the design needs simplification.

---

## Test Organization

### Structure

```
tests/
  unit/
    test_core.py        # Business logic tests
    test_validators.py  # Validation tests
  integration/
    test_cli.py         # CLI invocation tests
  contract/
    test_api_contracts.py  # External API contracts
  conftest.py           # Shared fixtures
```

### Naming Conventions

- Files: `test_<module>.py`
- Functions: `test_<unit>_<behavior>` or `test_<behavior>_when_<condition>`
- Classes (grouping): `TestClassName` for related tests

```python
# Descriptive test names
def test_process_file_raises_on_missing_input():
    ...

def test_parse_config_uses_defaults_when_optional_fields_missing():
    ...

# Grouped by class
class TestEmailValidator:
    def test_accepts_valid_email(self):
        ...

    def test_rejects_missing_domain(self):
        ...
```

---

## Test Types

### Unit Tests (Primary Focus)

Isolated, fast, test single units of behavior.

```python
# test_core.py
from src.core import calculate_total

def test_calculate_total_sums_items():
    items = [{"price": 10}, {"price": 20}]

    result = calculate_total(items)

    assert result == 30

def test_calculate_total_returns_zero_for_empty():
    result = calculate_total([])

    assert result == 0
```

**Characteristics:**
- No I/O (files, network, database)
- No external dependencies
- Execute in milliseconds
- Test one behavior per test

### Contract Tests (API Boundaries)

Verify external API contracts without calling real services.

```python
# test_api_contracts.py
import responses
from src.api_client import GitHubClient

class TestGitHubAPIContract:
    """Verify our code handles GitHub API responses correctly."""

    @responses.activate
    def test_get_user_parses_response(self):
        # Define expected contract
        responses.add(
            responses.GET,
            "https://api.github.com/users/octocat",
            json={"login": "octocat", "id": 1},
            status=200
        )

        client = GitHubClient()
        user = client.get_user("octocat")

        assert user.login == "octocat"
        assert user.id == 1

    @responses.activate
    def test_get_user_handles_not_found(self):
        responses.add(
            responses.GET,
            "https://api.github.com/users/nonexistent",
            json={"message": "Not Found"},
            status=404
        )

        client = GitHubClient()

        with pytest.raises(UserNotFoundError):
            client.get_user("nonexistent")
```

**Contract test principles:**
- Document expected external API behavior
- Catch breaking changes in dependencies
- Run fast (mocked responses)
- Cover success, error, and edge cases

### Integration Tests (CLI Layer)

Test command invocation and output formatting.

```python
# test_cli.py
from typer.testing import CliRunner
from src.cli import app

runner = CliRunner()

def test_cli_success_output(tmp_path):
    input_file = tmp_path / "data.txt"
    input_file.write_text("test content")

    result = runner.invoke(app, [str(input_file)])

    assert result.exit_code == 0
    assert "processed" in result.stdout.lower()

def test_cli_error_shows_message():
    result = runner.invoke(app, ["/nonexistent"])

    assert result.exit_code == 2
    assert "error" in result.stdout.lower()
```

---

## Test Structure (AAA Pattern)

Every test follows Arrange-Act-Assert:

```python
def test_parser_extracts_fields():
    # Arrange - Set up preconditions
    raw_data = {"name": "test", "value": 42}
    parser = DataParser()

    # Act - Execute the behavior under test
    result = parser.parse(raw_data)

    # Assert - Verify the outcome
    assert result.name == "test"
    assert result.value == 42
```

**Keep tests focused**: One logical assertion per test (multiple `assert` statements are fine if they verify one behavior).

---

## Mocking Strategy

### Mock External Dependencies Only

```python
# Good: Mock external HTTP calls
@responses.activate
def test_fetches_remote_config():
    responses.add(responses.GET, "https://api.example.com/config", json={"key": "value"})

    result = fetch_config()

    assert result["key"] == "value"

# Good: Mock file system for isolation
def test_reads_config_file(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("key: value")

    result = read_config(config_file)

    assert result["key"] == "value"
```

### Never Mock the System Under Test

```python
# Bad: Mocking the thing we're testing
def test_calculator(mocker):
    mocker.patch.object(Calculator, 'add', return_value=5)
    calc = Calculator()
    assert calc.add(2, 3) == 5  # Tests nothing!

# Good: Test real behavior
def test_calculator_adds():
    calc = Calculator()
    assert calc.add(2, 3) == 5
```

### Preferred Mocking Tools

- `tmp_path` fixture for file operations (built into pytest)
- `responses` library for HTTP mocking
- `pytest-mock` for general mocking when necessary
- `freezegun` for time-dependent tests

```python
# Example with freezegun
from freezegun import freeze_time

@freeze_time("2024-01-15")
def test_generates_dated_filename():
    result = generate_filename("report")

    assert result == "report_2024-01-15.txt"
```

---

## Fixtures and Factories

### Shared Fixtures in conftest.py

```python
# conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def sample_config():
    """Standard config for testing."""
    return {
        "name": "test-app",
        "version": "1.0.0",
        "debug": False
    }

@pytest.fixture
def temp_config_file(tmp_path, sample_config):
    """Config file in temp directory."""
    import json
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(sample_config))
    return config_path
```

### Factory Pattern for Complex Objects

```python
# conftest.py
@pytest.fixture
def make_user():
    """Factory for creating test users with defaults."""
    def _make_user(name="test", email="test@example.com", active=True):
        return User(name=name, email=email, active=active)
    return _make_user

# Usage in tests
def test_inactive_user_cannot_login(make_user):
    user = make_user(active=False)

    result = user.can_login()

    assert result is False
```

---

## Coverage

### Target: 90% Coverage

Configure in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "--cov=src --cov-report=term-missing --cov-fail-under=90"
testpaths = ["tests"]

[tool.coverage.run]
branch = true
source = ["src"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.:",
    "raise NotImplementedError",
]
```

### Coverage Philosophy

- 90% is minimum; aim higher for critical paths
- Coverage measures execution, not correctness
- Missing coverage = missing test, not always a problem
- Use `# pragma: no cover` sparingly and with justification

---

## Running Tests

### Common Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_core.py

# Run tests matching pattern
pytest -k "test_parse"

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x

# Run failed tests from last run
pytest --lf
```

### Fast Feedback Loop

For TDD, use watch mode:

```bash
# With pytest-watch
ptw -- --lf -x

# Or with entr
find src tests -name "*.py" | entr -c pytest --lf -x
```

---

## Anti-Patterns to Avoid

### 1. Testing Implementation Details

```python
# Bad: Tests internal structure
def test_cache_uses_dict():
    cache = Cache()
    assert isinstance(cache._storage, dict)

# Good: Tests behavior
def test_cache_returns_stored_value():
    cache = Cache()
    cache.set("key", "value")
    assert cache.get("key") == "value"
```

### 2. Excessive Mocking

```python
# Bad: Mock everything
def test_processor(mocker):
    mocker.patch("src.processor.validate")
    mocker.patch("src.processor.transform")
    mocker.patch("src.processor.save")
    processor = Processor()
    processor.run()  # Tests nothing meaningful

# Good: Integration test with minimal mocks
def test_processor_transforms_data(tmp_path):
    input_file = tmp_path / "input.txt"
    input_file.write_text("raw data")

    processor = Processor()
    result = processor.run(input_file)

    assert result == "transformed data"
```

### 3. Slow Tests

```python
# Bad: Real network calls
def test_api_response():
    response = requests.get("https://api.example.com/data")  # Slow, flaky
    assert response.status_code == 200

# Good: Mocked response
@responses.activate
def test_api_response():
    responses.add(responses.GET, "https://api.example.com/data", status=200)
    response = requests.get("https://api.example.com/data")
    assert response.status_code == 200
```

### 4. Test Interdependence

```python
# Bad: Tests depend on execution order
class TestStateful:
    data = []

    def test_add(self):
        self.data.append(1)
        assert len(self.data) == 1

    def test_check(self):
        assert len(self.data) == 1  # Fails if run alone!

# Good: Each test is independent
def test_add():
    data = []
    data.append(1)
    assert len(data) == 1
```

---

## TDD Workflow Summary

1. **Start with a test** that describes the desired behavior
2. **Run test** - confirm it fails (Red)
3. **Write minimal code** to pass the test (Green)
4. **Refactor** while keeping tests green
5. **Repeat** for next behavior

**Discipline**: Never write production code without a failing test first.

---

_Focus on test-first design and fast feedback. Tool configuration belongs in pyproject.toml._
