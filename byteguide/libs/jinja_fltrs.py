import typing as t

from jinja2.environment import Environment


def datetime_format(value, format="%Y-%m-%d"):
    return value.strftime(format)


def str_split(value: str, sep: str = " ", pick: int = 0) -> str:
    parts = value.split(sep)
    return parts[pick]


def register_filters():
    env = Environment()

    env.filters["datetime_format"] = datetime_format
    env.filters["str_split"] = str_split

    print("registered new jinja2 filters...")
    print(env.filters)
