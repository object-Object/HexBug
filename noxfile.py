import nox
from nox.command import CommandFailed

nox.options.reuse_existing_virtualenvs = True

nox.options.sessions = [
    "test",
]


# tests


@nox.session
def test(session: nox.Session):
    session.install("-e", ".[runtime,test]")
    install_hexnumgen(session)

    session.run("pytest", *session.posargs)


# dev sessions


@nox.session
def run(session: nox.Session):
    session.install("-e", ".[runtime]")
    install_hexnumgen(session)

    session.run("python", "main.py", env={"ENVIRONMENT": "dev"})


# helper functions


def install_hexnumgen(session: nox.Session):
    try:
        session.install("--find-links=./vendor", "hexnumgen")
    except CommandFailed:
        session.install("-e", ".[target-any]")
