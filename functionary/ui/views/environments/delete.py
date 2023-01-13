from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic.edit import DeleteView

from core.auth import Permission
from core.models import Environment, EnvironmentUserRole


class EnvironmentUserRoleDeleteView(
    LoginRequiredMixin, UserPassesTestMixin, DeleteView
):
    model = EnvironmentUserRole

    def get_success_url(self) -> str:
        environment_user_role: EnvironmentUserRole = self.get_object()
        return reverse(
            "ui:environment-detail", kwargs={"pk": environment_user_role.environment.id}
        )

    def test_func(self) -> bool:
        environment = get_object_or_404(Environment, id=self.kwargs["environment_id"])
        return self.request.user.has_perm(Permission.ENVIRONMENT_UPDATE, environment)
