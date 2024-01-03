from typing import Optional

import boto3
from mypy_boto3_s3 import S3ServiceResource
from typer import Typer

app = Typer(
    pretty_exceptions_enable=False,
)


@app.command()
def main(
    bucket_name: str,
    prefix: str,
    *,
    keep: int = 5,
    profile: Optional[str] = None,
):
    session = boto3.Session(profile_name=profile)
    s3: S3ServiceResource = session.resource("s3")

    bucket = s3.Bucket(bucket_name)

    objects = sorted(
        bucket.objects.filter(Prefix=prefix),
        key=lambda o: o.last_modified,
        reverse=True,
    )
    for obj in objects[keep:]:
        print(f"Deleting object: {obj.key}")
        obj.delete()


if __name__ == "__main__":
    app()
