from typing import Union

from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import (
    PolymorphicProxySerializer,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from core.api import HEADER_PARAMETERS
from core.api.permissions import HasEnvironmentPermissionForAction
from core.api.v1.serializers import (
    TaskCreateByIdSerializer,
    TaskCreateByNameSerializer,
    TaskCreateResponseSerializer,
    TaskLogSerializer,
    TaskResultSerializer,
    TaskSerializer,
)
from core.api.v1.utils import PREFIX, SEPARATOR, get_parameter_name
from core.api.viewsets import EnvironmentGenericViewSet
from core.models import Task, TaskResult
from core.utils.minio import handle_file_parameters

RENDER_PREFIX = f"{PREFIX}{SEPARATOR}".replace("\\", "")


@extend_schema_view(
    retrieve=extend_schema(parameters=HEADER_PARAMETERS),
    list=extend_schema(parameters=HEADER_PARAMETERS),
)
class TaskViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    EnvironmentGenericViewSet,
):
    """View for creating and retrieving tasks"""

    queryset = Task.objects.all()
    parser_classes = [MultiPartParser]
    serializer_class = TaskSerializer
    permission_classes = [HasEnvironmentPermissionForAction]

    def get_serializer_class(self):
        if self.action == "create":
            if "function_name" in self.request.data.keys():
                return TaskCreateByNameSerializer
            else:
                return TaskCreateByIdSerializer
        else:
            return self.serializer_class

    @extend_schema(
        description=(
            "Execute a function. The function to be executed can be defined either "
            "by supplying function as a string uuid, or function_name and "
            "package_name. "
            "Parameters can be passed to the API either by prefixing them with "
            f"`{RENDER_PREFIX}`, or placing them inside a `parameters` JSON "
            "string. Prefixed parameters will **override** duplicate parameters "
            "inside the parameters JSON string."
        ),
        request=PolymorphicProxySerializer(
            component_name="TaskCreate",
            serializers={
                "create_by_id": TaskCreateByIdSerializer,
                "create_by_name": TaskCreateByNameSerializer,
            },
            resource_type_field_name=None,
        ),
        responses={
            status.HTTP_201_CREATED: TaskCreateResponseSerializer,
        },
        parameters=HEADER_PARAMETERS,
    )
    def create(self, request: Request, *args, **kwargs):
        data = request.data

        # Remove list elements that wrap singular values when multipart content
        data = request.data.dict()

        request_serializer: Union[
            TaskCreateByIdSerializer, TaskCreateByNameSerializer
        ] = self.get_serializer(data=data)

        request_serializer.is_valid(raise_exception=True)

        request_serializer.save(
            creator=self.request.user, environment=self.get_environment()
        )

        _handle_file_parameters(request, request_serializer)

        response_serializer = TaskCreateResponseSerializer(request_serializer.instance)

        headers = self.get_success_headers(response_serializer.data)

        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @extend_schema(
        description="Retrieve the task results",
        parameters=HEADER_PARAMETERS,
        responses={status.HTTP_200_OK: TaskResultSerializer},
    )
    @action(methods=["get"], detail=True)
    def result(self, request, pk=None):
        task = self.get_object()

        if not TaskResult.objects.filter(task=task).exists():
            raise NotFound(f"No result found for task {pk}.")

        serializer = TaskResultSerializer(task)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        description="Retrieve the task log output",
        parameters=HEADER_PARAMETERS,
        responses={status.HTTP_200_OK: TaskLogSerializer},
    )
    @action(methods=["get"], detail=True)
    def log(self, request, pk=None):
        task = self.get_object()

        try:
            serializer = TaskLogSerializer(task.tasklog)
        except ObjectDoesNotExist:
            raise NotFound(f"No log found for task {pk}.")

        return Response(serializer.data, status=status.HTTP_200_OK)


def _handle_file_parameters(
    request: Request,
    request_serializer: Union[TaskCreateByIdSerializer, TaskCreateByNameSerializer],
) -> None:
    """Mutate the file parameter names passed to the API

    Arguments:
        request: The originating API request
        request_serializer: The serializer that generated the task for the request

    Returns:
        None
    """
    if not request.FILES:
        return

    # Wrap items in list to avoid dictionary changed size error
    for param, _ in list(request.FILES.items()):
        if param_name := get_parameter_name(param):
            request.FILES[param_name] = request.FILES.pop(param)[0]

    task = Task.objects.get(id=request_serializer.instance.id)
    _upload_files(task, request)


def _upload_files(task: Task, request: Request) -> None:
    handle_file_parameters(task, request)
