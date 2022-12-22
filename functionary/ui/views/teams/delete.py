from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View

from core.auth import Permission
from core.models import Team, TeamUserRole, User


class TeamDeleteMemberView(LoginRequiredMixin, UserPassesTestMixin, View):
    def delete(self, request: HttpRequest, team_id: str, user_id: str):
        team = get_object_or_404(Team, id=team_id)
        user = get_object_or_404(User, id=user_id)

        _ = TeamUserRole.objects.get(user=user, team=team).delete()
        return HttpResponse("")

    def test_func(self) -> bool:
        team = get_object_or_404(Team, id=self.kwargs["team_id"])
        return self.request.user.has_perm(Permission.TEAM_UPDATE, team)
