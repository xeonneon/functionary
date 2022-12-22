from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View

from core.auth import Permission
from core.models import Environment, EnvironmentUserRole, User


class EnvironmentDeleteMemberView(LoginRequiredMixin, UserPassesTestMixin, View):
    def delete(self, request: HttpRequest, environment_id: str, user_id: str):
        environment = get_object_or_404(Environment, id=environment_id)
        user = get_object_or_404(User, id=user_id)

        _ = EnvironmentUserRole.objects.filter(
            user=user, environment=environment
        ).delete()
        return HttpResponse()

    def test_func(self) -> bool:
        environment = get_object_or_404(Environment, id=self.kwargs["environment_id"])
        return self.request.user.has_perm(Permission.ENVIRONMENT_UPDATE, environment)
