import logging

import aws_cdk as cdk
from aws_cdk import aws_codedeploy as codedeploy
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk_github_oidc import GithubActionsIdentityProvider, GithubActionsRole
from constructs import Construct

BASE_STACK_NAME = "HexBug"


class CDKStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        *,
        stage: str,
        env: cdk.Environment,
        artifacts_bucket_name: str,
        on_premise_instance_tag: str,
        oidc_owner: str,
        oidc_repo: str,
        oidc_environment: str,
    ):
        stack_name = f"{stage}-{BASE_STACK_NAME}"

        logging.getLogger(__name__).info(f"Initializing stack: {stack_name}")
        super().__init__(
            scope,
            stage,
            stack_name=stack_name,
            env=env,
        )

        # external resources

        oidc_proxy = GithubActionsIdentityProvider.from_account(self, "OIDCProxy")

        artifacts_bucket_proxy = s3.Bucket.from_bucket_name(
            self,
            "ArtifactsBucketProxy",
            artifacts_bucket_name,
        )

        # codedeploy application

        application = codedeploy.ServerApplication(self, "Application")

        deployment_config: codedeploy.ServerDeploymentConfig = (
            codedeploy.ServerDeploymentConfig.ONE_AT_A_TIME
        )

        deployment_group = codedeploy.ServerDeploymentGroup(
            self,
            "DeploymentGroup",
            application=application,
            deployment_config=deployment_config,
            auto_rollback=codedeploy.AutoRollbackConfig(
                failed_deployment=True,
            ),
            on_premise_instance_tags=codedeploy.InstanceTagSet(
                {"instance": [on_premise_instance_tag]}
            ),
        )

        # GitHub Actions

        github_actions_role = GithubActionsRole(
            self,
            "GitHubActionsRole",
            provider=oidc_proxy,
            owner=oidc_owner,
            repo=oidc_repo,
            filter=f"environment:{oidc_environment}",
        )
        artifacts_bucket_proxy.grant_read_write(github_actions_role)
        github_actions_role.add_to_policy(
            iam.PolicyStatement(
                actions=["codedeploy:*"],
                resources=[
                    application.application_arn,
                    deployment_group.deployment_group_arn,
                    deployment_config.deployment_config_arn,
                ],
            )
        )

        # outputs

        cdk.CfnOutput(
            self,
            "ApplicationName",
            value=application.application_name,
        )

        cdk.CfnOutput(
            self,
            "DeploymentGroupName",
            value=deployment_group.deployment_group_name,
        )

        cdk.CfnOutput(
            self,
            "GitHubActionsRoleARN",
            value=github_actions_role.role_arn,
        )
