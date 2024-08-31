import shutil
import sys
from pathlib import Path

import nox
from nox.command import CommandFailed

nox.options.default_venv_backend = "uv|virtualenv"
nox.options.reuse_existing_virtualenvs = True

nox.options.sessions = [
    "test",
]


# tests


@nox.session
def test(session: nox.Session):
    session.install("-e", ".[runtime,test]", "--find-links=./vendor")
    install_hexnumgen(session)

    session.run("pytest", *session.posargs)


# dev sessions


@nox.session
def run(session: nox.Session):
    session.install("-e", ".[runtime]", "--find-links=./vendor")
    install_hexnumgen(session)

    session.run("python", "main.py", env={"ENVIRONMENT": "dev"})


@nox.session(python=False)
def health_check(session: nox.Session):
    # fmt: off
    session.run(
        "docker", "compose", "exec",
        "--env", "HEALTH_CHECK_DISPLAY_NAME=Nox",
        "--env", "HEALTH_CHECK_PORT=40405",
        "--env", "HEALTH_CHECK_STARTUP_DELAY=4",
        "--env", "HEALTH_CHECK_ATTEMPTS=3",
        "--env", "HEALTH_CHECK_INTERVAL=5",
        "--env", "HEALTH_CHECK_TIMEOUT=6",
        "bot",
        "python", "scripts/bot/health_check.py",
        external=True,
    )
    # fmt: on


@nox.session
def scrape_book_types(session: nox.Session):
    session.install("-e", ".[runtime]", "--find-links=./vendor")

    tmp_file = Path("out/book_types.py")
    tmp_file.parent.mkdir(parents=True, exist_ok=True)
    with tmp_file.open("w", encoding="utf-8") as f:
        session.run(
            "python",
            "scripts/github/scrape_book_types.py",
            stdout=f,
            stderr=sys.stderr,
        )

    if not tmp_file.read_text("utf-8").strip():
        session.error("No output printed by script.")

    session.run("ruff", "format", tmp_file)
    session.run("ruff", "check", "--select=I", "--fix", tmp_file)

    shutil.move(tmp_file, "src/HexBug/utils/book_types.py")


# helper functions


def install_hexnumgen(session: nox.Session):
    try:
        session.install("--find-links=./vendor", "hexnumgen")
    except CommandFailed:
        session.install("-e", ".[target-any]")
