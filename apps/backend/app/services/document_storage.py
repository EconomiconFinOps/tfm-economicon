"""Bounded S3 operations; staging URLs never grant access to confirmed objects.

Kept identical in backend and processor (independent Python deployments).
"""
from dataclasses import dataclass, field
import hashlib
import os
import re
from urllib.parse import urlsplit


MAX_FILE_BYTES = 20_000_000


class StorageUnavailable(RuntimeError):
    pass


class InvalidDocument(ValueError):
    pass


@dataclass(frozen=True)
class StorageConfig:
    bucket: str
    endpoint: str
    public_endpoint: str
    region: str
    access_key: str | None = field(repr=False)
    secret_key: str | None = field(repr=False)
    max_bytes: int = MAX_FILE_BYTES
    url_seconds: int = 180
    auth_mode: str = 'static'

    def __post_init__(self):
        if self.auth_mode not in {'static', 'iam'}:
            raise ValueError('Invalid document storage authentication mode')
        if self.auth_mode == 'iam':
            endpoint = 'https://s3.eu-west-1.amazonaws.com'
            if (self.region != 'eu-west-1' or self.endpoint != endpoint
                    or self.public_endpoint != endpoint or self.access_key or self.secret_key
                    or not re.fullmatch(r'[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]', self.bucket)):
                raise ValueError('IAM document storage requires the reviewed regional endpoint and task credentials')

    @classmethod
    def from_env(cls):
        maximum = int(os.getenv('DOCUMENT_MAX_FILE_BYTES', str(MAX_FILE_BYTES)))
        seconds = int(os.getenv('DOCUMENT_UPLOAD_URL_SECONDS', '180'))
        if not 1 <= maximum <= MAX_FILE_BYTES or not 30 <= seconds <= 900:
            raise ValueError('Invalid document limits')
        endpoint = os.environ['DOCUMENT_S3_ENDPOINT']
        public = os.getenv('DOCUMENT_S3_PUBLIC_ENDPOINT', endpoint)
        for value in (endpoint, public):
            parsed = urlsplit(value)
            if (parsed.scheme not in {'http', 'https'} or not parsed.hostname
                    or parsed.username or parsed.password or parsed.query or parsed.fragment
                    or parsed.path not in {'', '/'}):
                raise ValueError('Invalid document storage endpoint')
            if os.getenv('RUNTIME_ENVIRONMENT', 'production') == 'production' and parsed.scheme != 'https':
                raise ValueError('Document storage requires HTTPS in production')
        mode = os.getenv('DOCUMENT_S3_AUTH_MODE', 'static')
        access = os.getenv('DOCUMENT_S3_ACCESS_KEY')
        secret = os.getenv('DOCUMENT_S3_SECRET_KEY')
        bucket = os.environ['DOCUMENT_S3_BUCKET']
        if (not bucket.strip() or (mode == 'static'
                and (not access or not access.strip() or not secret or not secret.strip()))):
            raise ValueError('Document storage credentials and bucket are required')
        return cls(bucket, endpoint, public, os.getenv('DOCUMENT_S3_REGION', 'us-east-1'), access, secret, maximum, seconds, mode)


class S3Storage:
    def __init__(self, config=None):
        import boto3
        from botocore.config import Config
        self.config = config or StorageConfig.from_env()
        sdk_options = {'ignore_configured_endpoint_urls': True, 'proxies': {}} if self.config.auth_mode == 'iam' else {}
        options = dict(region_name=self.config.region,
                       config=Config(signature_version='s3v4', s3={'addressing_style': 'path'},
                                     **sdk_options,
                                     connect_timeout=5, read_timeout=15, retries={'max_attempts': 1}))
        if self.config.auth_mode == 'static':
            options.update(aws_access_key_id=self.config.access_key, aws_secret_access_key=self.config.secret_key)
        self.internal = boto3.client('s3', endpoint_url=self.config.endpoint, **options)
        self.public = boto3.client('s3', endpoint_url=self.config.public_endpoint, **options)

    def presign(self, key, size):
        return self.public.generate_presigned_url('put_object', Params={
            'Bucket': self.config.bucket, 'Key': key, 'ContentType': 'application/octet-stream',
            'ContentLength': size,
        }, ExpiresIn=self.config.url_seconds, HttpMethod='PUT')

    def read(self, key, expected_size, expected_hash):
        from botocore.exceptions import ClientError
        response = None
        try:
            response = self.internal.get_object(Bucket=self.config.bucket, Key=key)
            if response['ContentLength'] != expected_size or not 0 < response['ContentLength'] <= self.config.max_bytes:
                raise InvalidDocument('document_size_mismatch')
            data = response['Body'].read(self.config.max_bytes + 1)
            if len(data) != expected_size or hashlib.sha256(data).hexdigest() != expected_hash:
                raise InvalidDocument('document_integrity_mismatch')
            return data
        except InvalidDocument:
            raise
        except ClientError as error:
            if error.response['Error']['Code'] in {'NoSuchKey', '404'}:
                raise InvalidDocument('document_object_missing') from None
            raise StorageUnavailable('document_storage_unavailable') from None
        except Exception:
            raise StorageUnavailable('document_storage_unavailable') from None
        finally:
            if response is not None:
                response['Body'].close()

    def finalize(self, key, data, digest):
        from botocore.exceptions import ClientError
        try:
            self.internal.put_object(Bucket=self.config.bucket, Key=key, Body=data,
                                     ContentType='application/octet-stream', Metadata={'sha256': digest},
                                     IfNoneMatch='*')
        except ClientError as error:
            if error.response['Error']['Code'] in {'PreconditionFailed', '412'}:
                # Concurrent confirmation may have finalized this exact session already.
                self.read(key, len(data), digest)
                return
            raise StorageUnavailable('document_storage_unavailable') from None
        except Exception:
            raise StorageUnavailable('document_storage_unavailable') from None

    def delete(self, key):
        try:
            self.internal.delete_object(Bucket=self.config.bucket, Key=key)
        except Exception:
            raise StorageUnavailable('document_storage_unavailable') from None

    def close(self):
        self.internal.close()
        self.public.close()
