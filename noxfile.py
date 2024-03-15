import nox

nox.options.reuse_existing_virtualenvs = True

nox.options.sessions = [
    "test",
]


@nox.session
def test(session: nox.Session):
    session.install("-e", ".[runtime,target-any,test]")

    session.run("pytest", *session.posargs)
