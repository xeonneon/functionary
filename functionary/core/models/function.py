""" Function model """
import uuid
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db import models

from core.utils.parameter import get_schema

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from core.models import ScheduledTask


def list_of_strings(value):
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return

    raise ValidationError(
        '"%(value)s" is not a list of strings', params={"value": value}
    )


class Function(models.Model):
    """Function is a unit of work that can be tasked

    Attributes:
        id: unique identifier (UUID)
        package: the package that the function is a part of
        environment: the environment the function is associated with
        name: internal name that published package definition keys off of
        display_name: optional display name
        summary: short description of the function
        description: more details about the function
        variables: list of variable names to set before execution
        return_type: the type of the object being returned
        active: whether the function is currently activated
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    package = models.ForeignKey(
        to="Package", on_delete=models.CASCADE, related_name="functions"
    )
    environment = models.ForeignKey(to="Environment", on_delete=models.CASCADE)

    name = models.CharField(max_length=64, blank=False, editable=False)
    display_name = models.CharField(max_length=64, null=True)
    summary = models.CharField(max_length=128, null=True)
    description = models.TextField(null=True)
    variables = models.JSONField(default=list, validators=[list_of_strings])
    return_type = models.CharField(max_length=64, null=True)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["package", "name"], name="package_name_unique_together"
            )
        ]
        indexes = [
            models.Index(
                fields=["environment", "name"], name="function_environment_name"
            )
        ]

    def __str__(self):
        return self.name

    def _clean_environment(self):
        if self.environment is None:
            self.environment = self.package.environment
        elif self.environment != self.package.environment:
            raise ValidationError(
                "Function environment must match Package environment.", code="invalid"
            )

    def _clean_active_status(self):
        # NOTE: If a Function's package is disabled, the function is considered disabled
        if not self.package.is_enabled() and self.active:
            raise ValidationError(
                "Function's package is currently disabled.", code="invalid"
            )

    def clean(self):
        self._clean_environment()
        self._clean_active_status()

    def activate(self, update_status: bool = True):
        """Activate the function and any associated scheduled tasks"""

        # If the function is not active, and the function's package is enabled,
        # then the function can be activated
        if not self.active and self.package.is_enabled():
            if update_status:
                self.active = True
                self.save()

            for scheduled_task in self.associated_scheduled_tasks:
                scheduled_task.activate()

    def deactivate(self, update_status: bool = True):
        """Deactivate the function and pause any associated scheduled tasks"""
        if self.active:
            if update_status:
                self.active = False
                self.save()

            for scheduled_task in self.associated_scheduled_tasks:
                scheduled_task.pause()

    @property
    def parameters(self):
        """Convenience alias for functionparameter_set"""
        # Provides better static type checking than using related_name
        return self.functionparameter_set

    @property
    def render_name(self) -> str:
        """Returns the template-renderable name of the function"""
        return self.display_name if self.display_name else self.name

    @property
    def schema(self) -> dict:
        """Function definition schema"""
        return get_schema(self)

    @property
    def associated_scheduled_tasks(self) -> "QuerySet[ScheduledTask]":
        """Get all associated scheduled tasks for this function"""
        return self.scheduled_tasks.all()
