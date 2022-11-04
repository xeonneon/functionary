""" Scheduled Task model """
import uuid

import jsonschema
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils import timezone
from django_celery_beat.models import PeriodicTask

from core.models import ModelSaveHookMixin


class ScheduledTask(ModelSaveHookMixin, models.Model):
    """A ScheduledTask is the scheduled execution of a task
    This model should always be queried with environment as one of the filter
    parameters. The indices are intentionally setup this way as all requests for task
    data happen in the context of a specific environment.
    Attributes:
        id: unique identifier (UUID)
        function: the function that this task is an execution of
        environment: the environment that this task belongs to. All queryset filtering
                     should include an environment.
        parameters: JSON representing the parameters that will be passed to the function
        creator: the user that initiated the task
        created_at: task creation timestamp
        updated_at: task updated timestamp
        periodic_task: The celery-beat periodic-task associated with this scheduled task
    """

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    ARCHIVED = "ARCHIVED"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (ACTIVE, "Active"),
        (PAUSED, "Paused"),
        (ERROR, "Error"),
        (ARCHIVED, "Archived"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, blank=False)
    description = models.TextField(blank=True)
    function = models.ForeignKey(to="Function", on_delete=models.CASCADE)
    environment = models.ForeignKey(to="Environment", on_delete=models.CASCADE)
    parameters = models.JSONField(encoder=DjangoJSONEncoder)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=PENDING)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_run_at = models.DateTimeField(blank=True, null=True)
    periodic_task = models.ForeignKey(
        to=PeriodicTask, null=True, blank=True, on_delete=models.CASCADE
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["environment", "function"], name="s_task_environment_function"
            ),
            models.Index(
                fields=["environment", "creator"], name="s_task_environment_creator"
            ),
            models.Index(
                fields=["environment", "created_at"],
                name="s_task_environment_created_at",
            ),
            models.Index(
                fields=["environment", "updated_at"],
                name="s_task_environment_updated_at",
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

    def _clean_parameters(self):
        """Validate that the parameters conform to the function's schema"""
        try:
            jsonschema.validate(
                instance=self.parameters,
                schema=self.function.schema,
            )
        except jsonschema.ValidationError as exc:
            raise ValidationError(exc.message)

    def clean(self):
        """Model instance validation and attribute cleanup"""
        self._clean_environment()
        self._clean_parameters()

    def activate(self) -> None:
        self._enable_periodic_task()
        self._update_status(self.ACTIVE)

    def pause(self) -> None:
        self._disable_periodic_task()
        self._update_status(self.PAUSED)

    def error(self) -> None:
        self._disable_periodic_task()
        self._update_status(self.ERROR)

    def archive(self) -> None:
        self._disable_periodic_task()
        self._update_status(self.ARCHIVED)

    def update_last_run_at(self) -> None:
        self.last_run_at = timezone.now()
        self.save()

    def _enable_periodic_task(self) -> None:
        if self.periodic_task is None:
            return
        self.periodic_task.enabled = True
        self.periodic_task.save()

    def _disable_periodic_task(self) -> None:
        if self.periodic_task is None:
            return
        self.periodic_task.enabled = False
        self.periodic_task.save()

    def _update_status(self, status: str) -> None:
        if self.periodic_task is None:
            return
        self.status = status
        self.save()
