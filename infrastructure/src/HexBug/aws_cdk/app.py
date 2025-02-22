import logging

from object_ci.aws_cdk.codedeploy.stack import CodeDeployStack
from object_ci.logging import setup_logging

import aws_cdk as cdk

logger = logging.getLogger(__name__)


def main():
    setup_logging()

    logger.info("Ready.")
    app = cdk.App()

    CodeDeployStack.default_prod_stack(app)

    logger.info("Synthesizing.")
    app.synth()


if __name__ == "__main__":
    main()
