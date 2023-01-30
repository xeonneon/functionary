from datetime import timedelta
from io import BytesIO
from os import getenv

from django.http import HttpRequest
from minio import Minio
from urllib3.response import HTTPResponse

from core.models import Environment


class MinioInterface:
    def __init__(self, bucket_name: str):
        self.client = Minio(
            endpoint=f"{getenv('MINIO_HOST')}:{getenv('MINIO_PORT')}",
            access_key=getenv("MINIO_ROOT_USER"),
            secret_key=getenv("MINIO_ROOT_PASSWORD"),
            secure=False,
        )
        self.bucket_name = bucket_name
        self._create_bucket()

    def bucket_exists(self) -> bool:
        return self.client.bucket_exists(self.bucket_name)

    def put_file(self, file: BytesIO, length: int, filename: str) -> None:
        _ = self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=filename,
            data=file,
            length=length,
        )

    def get_filenames(self, filename: str) -> list[str]:
        objects = self.client.list_objects(self.bucket_name)
        object_names = []
        for object in objects:
            object_names.append(object.object_name)
        return object_names

    def does_file_exist(self, filename: str) -> bool:
        objects = self.get_filenames(filename)
        return filename in objects

    def get_object(self, filename: str) -> HTTPResponse:
        try:
            if not self.does_file_exist(filename):
                return None
            response: HTTPResponse = self.client.get_object(self.bucket_name, filename)
            return response
        finally:
            response.close()
            response.release_conn()

    def get_presigned_url(self, filename: str) -> str:
        if self.bucket_exists():
            return self.client.get_presigned_url(
                method="GET",
                bucket_name=self.bucket_name,
                object_name=filename,
                expires=timedelta(minutes=5),
            )

    def _create_bucket(self) -> None:
        if self.bucket_exists():
            return
        self.client.make_bucket(self.bucket_name)

    def delete_bucket(self) -> None:
        if self.bucket_exists():
            self.client.remove_bucket(self.bucket_name)


def handle_file_parameters(
    environment: Environment,
    request: HttpRequest,
) -> None:
    """Uploads any files in the incoming request to an S3 bucket

    This function will check the request for any files. Each file will
    be uploaded to an S3 bucket that matches the environment ID.
    The file's name will be the same, so to access the file in Minio, you
    would go to <environment_id>/filename

    Arguments:
        environment: The environment the request was made from
        request: The HttpRequest that the form came from

    Returns:
        None
    """
    minio = MinioInterface(bucket_name=str(environment.id))
    if request.FILES:
        for _, file in request.FILES.items():
            minio.put_file(file=file.file, length=file.size, filename=file.name)
