"""Development configuration."""


def get():
    """
    Get the development configuration.

    Returns:
        The development configuration.
    """
    return {
        "port": 29001,
        "debug": True,
        "readonly": False,
    }
