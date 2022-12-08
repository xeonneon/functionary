from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse, HttpResponseNotModified
from django.shortcuts import get_object_or_404
from django.views.generic import View

from core.auth import Permission
from core.models import Environment, EnvironmentUserRole, User

from .utils import get_team_members


class EnvironmentDeleteMemberView(LoginRequiredMixin, UserPassesTestMixin, View):
    def delete(self, request: HttpRequest, environment_id: str, user_id: str):
        environment = get_object_or_404(Environment, id=environment_id)
        user = get_object_or_404(User, id=user_id)

        # Prevent team members from getting deleted from an environment
        if user in get_team_members(environment)[0]:
            return HttpResponseNotModified()

        _ = EnvironmentUserRole.objects.get(user=user, environment=environment).delete()
        return HttpResponse()

    def test_func(self) -> bool:
        environment = get_object_or_404(Environment, id=self.kwargs["environment_id"])
        return self.request.user.has_perm(Permission.ENVIRONMENT_UPDATE, environment)
