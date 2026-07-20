import logging
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from flask import current_app

logger = logging.getLogger(__name__)


class RemoteStorageService:
    # Encapsula la comunicacion con almacenamiento S3-compatible (Cloudflare R2). Es una capa de resiliencia adicional sobre el almacenamiento local ya existente, nunca el mecanismo unico, si R2 no esta configurado o falla, el backup local generado por BackupService sigue siendo valido.

    @classmethod
    def _get_client(cls):
        endpoint = current_app.config.get("R2_ENDPOINT_URL")
        access_key = current_app.config.get("R2_ACCESS_KEY_ID")
        secret_key = current_app.config.get("R2_SECRET_ACCESS_KEY")
        bucket = current_app.config.get("R2_BUCKET_NAME")
        if not all([endpoint, access_key, secret_key, bucket]):
            return None
        return boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    @classmethod
    def is_configured(cls) -> bool:
        return cls._get_client() is not None

    @classmethod
    def upload_backup(cls, filepath: str, filename: str) -> bool:
        client = cls._get_client()
        if not client:
            logger.warning(
                "R2 no esta configurado, se omite la subida remota del respaldo %s.",
                filename,
            )
            return False
        bucket = current_app.config.get("R2_BUCKET_NAME")
        try:
            client.upload_file(filepath, bucket, filename)
            logger.info("Respaldo %s subido correctamente a R2.", filename)
            return True
        except (ClientError, EndpointConnectionError) as e:
            logger.error("Fallo al subir respaldo %s a R2: %s", filename, str(e))
            return False

    @classmethod
    def download_backup(cls, filename: str, destination_path: str) -> bool:
        client = cls._get_client()
        if not client:
            logger.warning(
                "R2 no esta configurado, no se puede descargar el respaldo %s.",
                filename,
            )
            return False
        bucket = current_app.config.get("R2_BUCKET_NAME")
        try:
            client.download_file(bucket, filename, destination_path)
            logger.info("Respaldo %s descargado correctamente desde R2.", filename)
            return True
        except (ClientError, EndpointConnectionError) as e:
            logger.error("Fallo al descargar respaldo %s desde R2: %s", filename, str(e))
            return False
