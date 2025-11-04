import os

class EnvConfig:

    @staticmethod
    def get_str(name: str) -> str:
        env = os.getenv(name)
        if env is None:
            raise RuntimeError(f'env {env} not found')
        return env
