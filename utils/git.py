import subprocess


def get_current_commit(path: str | None = None) -> str:
    result = subprocess.run(["git", "rev-parse", "--short=10", "HEAD"], capture_output=True, text=True, cwd=path)
    assert not result.stderr
    return result.stdout[:-1]
