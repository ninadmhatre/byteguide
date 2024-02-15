""" Configuration handler. """
import os
import typing as t
from functools import lru_cache

from . import default, development, production


class Config:
    """
    Represents a configuration object.
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._attributes(kwargs)

    def _attributes(self, kwargs: t.Dict[str, t.Any]):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f"Config({self.kwargs})"

    def __getattr__(self, name):
        """
        This method is called when an attribute is not found.
        It allows dynamic access to the configuration options.
        """
        return self.__dict__[name]


@lru_cache()
def get_instance_config(instance: t.Optional[str] = None) -> Config:
    """
    Get the instance config.

    Args:
        instance: The instance to use. If not provided, the `BYTEGUIDE_RUNENV` env var is used.

    Returns:
        The instance config.
    """
    env_ = instance or os.environ.get("BYTEGUIDE_RUNENV", "dev")

    assert env_, (
        "Yo.. you did not pass the config instance or forgot to set a RUNENV variable! "
        "(or maybe you did not read the docs?)"
    )

    env_map = {"dev": development, "prod": production}

    default_config = default.get()
    env_specific = env_map[env_].get()

    final_config = {**default_config, **env_specific}
    instance_config = Config(**final_config)

    print(f"Using config: {instance_config}")
    return instance_config


config = get_instance_config()
