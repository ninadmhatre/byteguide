""" Custom Jinja2 filters for the application. """
from jinja2.environment import Environment


def datetime_format(value, date_format="%Y-%m-%d"):
    """Format a datetime object to a string."""
    return value.strftime(date_format)


def str_split(value: str, sep: str = " ", pick: int = 0) -> str:
    """Split a string and return a part of it."""
    parts = value.split(sep)
    return parts[pick]


def register_filters():
    """Register the custom Jinja2 filters."""
    env = Environment()

    env.filters["datetime_format"] = datetime_format
    env.filters["str_split"] = str_split

    print("registered new jinja2 filters...")
    print(env.filters)
