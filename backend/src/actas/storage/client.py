"""MinIO / S3-compatible storage client."""

from __future__ import annotations

import logging
from typing import IO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from actas.settings import get_settings

logger = logging.getLogger(__name__)


class StorageClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._s3 = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=Config(
                signature_version="s3v4",
                connect_timeout=5,
                read_timeout=30,
                retries={"max_attempts": 3},
            ),
        )
        self._bucket = settings.S3_BUCKET

    # ── Bucket management ────────────────────────────────────────────────────

    def ensure_bucket(self) -> None:
        """Create the bucket if it doesn't exist."""
        try:
            self._s3.head_bucket(Bucket=self._bucket)
        except ClientError as exc:
            code = exc.response["Error"]["Code"]
            if code in ("404", "NoSuchBucket"):
                self._s3.create_bucket(Bucket=self._bucket)
                logger.info("Bucket '%s' creado.", self._bucket)
            else:
                raise

    # ── Upload ───────────────────────────────────────────────────────────────

    def upload_file(self, local_path: str, key: str) -> str:
        """Upload a local file. Returns the s3:// URI."""
        self._s3.upload_file(local_path, self._bucket, key)
        return f"s3://{self._bucket}/{key}"

    def upload_fileobj(
        self,
        fileobj: IO[bytes],
        key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload a file-like object. Returns the s3:// URI."""
        self._s3.upload_fileobj(
            fileobj,
            self._bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        return f"s3://{self._bucket}/{key}"

    # ── Download ─────────────────────────────────────────────────────────────

    def download_file(self, key: str, local_path: str) -> None:
        """Download an object to a local path."""
        self._s3.download_file(self._bucket, key, local_path)

    # ── Presigned URLs ────────────────────────────────────────────────────────

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a presigned GET URL valid for `expires_in` seconds."""
        return self._s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def uri_to_key(self, uri: str) -> str:
        """Extract the object key from an s3://bucket/key URI."""
        prefix = f"s3://{self._bucket}/"
        if uri.startswith(prefix):
            return uri[len(prefix):]
        # Fallback: strip leading slash
        return uri.lstrip("/")


# ── Module-level singleton ────────────────────────────────────────────────────

_client: StorageClient | None = None


def get_storage() -> StorageClient:
    global _client
    if _client is None:
        _client = StorageClient()
    return _client
