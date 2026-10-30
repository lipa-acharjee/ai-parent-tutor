from app.core.config import settings
from urllib.parse import urlparse

for name, value in [
    ("S3_ENDPOINT_URL", settings.s3_endpoint_url),
    ("S3_PUBLIC_ENDPOINT_URL", settings.s3_public_endpoint_url),
]:
    parsed = urlparse(value or "")
    print(f"{name}: scheme={parsed.scheme}, host={parsed.hostname}, path={parsed.path}")

print("AWS_REGION:", settings.aws_region)
print("S3_BUCKET:", settings.s3_bucket)
print("S3_ACCESS_KEY configured:", bool(settings.s3_access_key))
print("S3_SECRET_KEY configured:", bool(settings.s3_secret_key))
