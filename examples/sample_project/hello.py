"""Sample project — demonstrates a minimal C5-compliant repo."""


def greet(name: str = "sample_project") -> str:
    """Return a greeting string."""
    return f"Hello from {name}!"


if __name__ == "__main__":
    print(greet())
