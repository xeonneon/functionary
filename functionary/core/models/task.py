""" Task model """
import uuid
from json import JSONDecodeError
from typing import Optional, Union

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from core.models import ModelSaveHookMixin, ScheduledTask
from core.utils.parameter import validate_parameters


class PackageDisabledError(ValidationError):
    pass


class Task(ModelSaveHookMixin, models.Model):
    """A Task is an individual execution of a function

    This model should always be queried with environment as one of the filter
    parameters. The indices are intentionally setup this way as all requests for task
    data happen in the context of a specific environment.

    Attributes:
        id: unique identifier (UUID)
        function: the function that this task is an execution of
        environment: the environment that this task belongs to. All queryset filtering
                     should include an environment.
        parameters: JSON representing the parameters that will be passed to the function
        status: tasking status
        creator: the user that initiated the task
        created_at: task creation timestamp
        updated_at: task updated timestamp
    """

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (IN_PROGRESS, "In Progress"),
        (COMPLETE, "Complete"),
        (ERROR, "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    function = models.ForeignKey(to="Function", on_delete=models.CASCADE)
    environment = models.ForeignKey(to="Environment", on_delete=models.CASCADE)
    parameters = models.JSONField(encoder=DjangoJSONEncoder)
    return_type = models.CharField(max_length=64, null=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=PENDING)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    scheduled_task = models.ForeignKey(
        ScheduledTask, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["environment", "status"], name="task_environment_status"
            ),
            models.Index(
                fields=["environment", "creator"], name="task_environment_creator"
            ),
            models.Index(
                fields=["environment", "created_at"], name="task_environment_created_at"
            ),
            models.Index(
                fields=["environment", "updated_at"], name="task_environment_updated_at"
            ),
        ]

    def __str__(self):
        return str(self.id)

    def _clean_environment(self):
        """Ensures that the environment is correctly set to that of the function"""
        if self.environment is None:
            self.environment = self.function.package.environment
        elif self.environment != self.function.package.environment:
            raise ValidationError(
                "Function does not belong to the provided environment"
            )

    def _clean_active_status(self):
        # NOTE: If a Function's package is disabled, the function is considered disabled
        if not self.function.package.is_enabled():
            raise PackageDisabledError(
                "Function's package is currently disabled.", code="invalid"
            )

    def _clean_parameters(self):
        """Validate that the parameters conform to the function's schema"""
        validate_parameters(self.parameters, self.function)

    def _clean_function(self):
        """Validate function is active for newly created tasks"""
        if self._state.adding and self.function.active is False:
            raise ValidationError("This function is not active")

    def clean(self):
        """Model instance validation and attribute cleanup"""
        self._clean_environment()
        self._clean_active_status()
        self._clean_parameters()
        self._clean_function()

    def post_create(self):
        """Post create hooks"""
        from core.utils.tasking import publish_task

        publish_task.delay(self.id)

    @property
    def raw_result(self) -> Optional[str]:
        """Convenience property for accessing the result output"""
        try:
            return self.taskresult.result
        except ObjectDoesNotExist:
            return None

    @property
    def result(self) -> Optional[Union[bool, dict, float, int, list, str]]:
        """Convenience property for accessing the result output loaded as JSON"""
        try:
            return self.taskresult.json
        except ObjectDoesNotExist:
            return None
        except JSONDecodeError:
            return self.taskresult.result

    @property
    def log(self) -> Optional[str]:
        """Convenience property for accessing the log output"""
        try:
            return self.tasklog.log
        except ObjectDoesNotExist:
            return None

    @property
    def variables(self):
        """Returns the variables required by the function being tasked."""
        return self.environment.variables.filter(name__in=self.function.variables)
