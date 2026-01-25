"""Core business logic for TryAlma."""


def get_greeting(name: str) -> str:
    """Generate a greeting message.

    Args:
        name: The name to greet.

    Returns:
        A greeting string.
    """
    if not name or not name.strip():
        return "Hello, World!"
    return f"Hello, {name.strip()}!"
