from functools import lru_cache
import typing as t
import os

from . import development, production, default

class Config:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._attributes(kwargs)

    def _attributes(self, kwargs: t.Dict[str, t.Any]):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f"Config({self.kwargs})"
    
@lru_cache()
def get_instance_config(instance: t.Optional[str] = None) -> Config:
    env_ = instance or os.environ.get("BYTEGUIDE_RUNENV", "dev")

    assert (
        env_
    ), "Yo.. you did not pass the config instance or forgot set a RUNENV variable! (or maybe you did not read the docs?)"

    env_map = {"dev": development, "prod": production}

    default_config = default.get()
    env_specific = env_map[env_].get()

    final_config = {**default_config, **env_specific}
    config = Config(**final_config)

    print(f"Using config: {config}")
    return config

config = get_instance_config()
