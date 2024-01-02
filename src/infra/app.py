import logging
from typing import TypedDict

import aws_cdk as cdk

from .stack import CDKStack

logger = logging.getLogger(__name__)


class CommonKwargs(TypedDict):
    oidc_owner: str
    oidc_repo: str


def main():
    setup_logging()

    logger.info("Ready.")
    app = cdk.App()

    common = CommonKwargs(
        oidc_owner="object-Object",
        oidc_repo="HexBug",
    )

    CDKStack(
        app,
        stage="prod",
        env=cdk.Environment(
            account="511603859520",
            region="us-east-1",
        ),
        artifacts_bucket_name="prod-objectobject-ca-codedeploy-artifacts",
        on_premise_instance_tag="prod-objectobject-ca",
        oidc_environment="prod-codedeploy",
        **common,
    )

    logger.info("Synthesizing.")
    app.synth()


def setup_logging(verbose: bool = False):
    if verbose:
        level = logging.DEBUG
        fmt = "[{asctime} | {name} | {levelname}] {message}"
    else:
        level = logging.INFO
        fmt = "[{levelname}] {message}"

    logging.basicConfig(
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
        format=fmt,
        level=level,
    )
    logging.getLogger(__name__).debug("Logger initialized.")


if __name__ == "__main__":
    main()
