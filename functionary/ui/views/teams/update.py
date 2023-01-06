from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic.edit import UpdateView

from core.auth import Permission
from core.models import Team, TeamUserRole
from ui.forms.teams import TeamUserRoleForm


class TeamUpdateMemberView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = TeamUserRole
    form_class = TeamUserRoleForm
    template_name = "forms/teamuserrole_create_or_update.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        team_user_role: TeamUserRole = self.get_object()

        # Use string of id field if it is a UUID
        context["team_id"] = str(team_user_role.team.id)
        context["team_user_role_id"] = team_user_role.id
        context["username"] = team_user_role.user.username
        context["user_id"] = team_user_role.user.id
        return context

    def get_success_url(self) -> str:
        team_user_role: TeamUserRole = self.get_object()
        return reverse("ui:team-detail", kwargs={"pk": team_user_role.team.id})

    def test_func(self) -> bool:
        team = get_object_or_404(Team, id=self.kwargs["team_id"])
        return self.request.user.has_perm(Permission.TEAM_UPDATE, team)
