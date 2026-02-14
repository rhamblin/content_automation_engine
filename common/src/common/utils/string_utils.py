import re


def to_camel_case(value: str) -> str:
    """Convert a string to CamelCase, splitting on spaces and underscores."""
    return "".join(w.capitalize() for w in re.split(r"[\s_]+", value))
