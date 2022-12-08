from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View

from core.auth import Permission
from core.models import Environment, EnvironmentUserRole, Team, TeamUserRole, User


class TeamDeleteMemberView(LoginRequiredMixin, UserPassesTestMixin, View):
    def delete(self, request: HttpRequest, team_id: str, user_id: str):
        team = get_object_or_404(Team, id=team_id)
        user = get_object_or_404(User, id=user_id)

        _ = TeamUserRole.objects.get(user=user, team=team).delete()

        """
        Delete all inherited relationships for the user
        within all environments owned by the team.
        """
        environments = Environment.objects.filter(team=team)
        for environment in environments:
            _ = EnvironmentUserRole.objects.filter(
                user=user, environment=environment, inherited=True
            ).delete()

        return HttpResponse("")

    def test_func(self) -> bool:
        team = get_object_or_404(Team, id=self.kwargs["team_id"])
        return self.request.user.has_perm(Permission.TEAM_UPDATE, team)
