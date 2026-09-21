import boto3
from botocore.client import Config
from app.core.config import settings


class Storage:

    def __init__(self):

        common = {
            "region_name": settings.aws_region,
            "aws_access_key_id": settings.s3_access_key,
            "aws_secret_access_key": settings.s3_secret_key,
            "config": Config(signature_version="s3v4"),
        }

        # Client used INSIDE Docker
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            **common,
        )

        # Client used to generate URLs for the browser
        self.public_client = boto3.client(
            "s3",
            endpoint_url=settings.s3_public_endpoint_url,
            **common,
        )

    def put(self, key, body, content_type):

        self.client.put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
        )

    def delete(self, key):

        self.client.delete_object(
            Bucket=settings.s3_bucket,
            Key=key,
        )

    def presign_get(self, key, expires=900):

        return self.public_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.s3_bucket,
                "Key": key,
            },
            ExpiresIn=expires,
        )


storage = Storage()