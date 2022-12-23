from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.detail import DetailView

from core.auth import ROLE_HEIRARCHY_MAP, Permission
from core.models import Team, Variable


class TeamDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Team

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team: Team = self.get_object()
        users = [user_role for user_role in team.user_roles.all()]

        # Sort users by their role in decending order
        users.sort(
            key=lambda x: ROLE_HEIRARCHY_MAP.get(x.role.upper()).value, reverse=True
        )

        context["team_create_perm"] = (
            True
            if (self.request.user.has_perm(Permission.TEAM_UPDATE, team))
            else False
        )
        context["team_id"] = str(team.id)
        context["environments"] = team.environments.all()
        context["users"] = users
        context["var_create"] = self.request.user.has_perm(
            Permission.VARIABLE_CREATE, team
        )
        context["var_update"] = self.request.user.has_perm(
            Permission.VARIABLE_UPDATE, team
        )
        context["var_delete"] = self.request.user.has_perm(
            Permission.VARIABLE_DELETE, team
        )
        context["variables"] = (
            team.vars
            if self.request.user.has_perm(Permission.VARIABLE_READ, team)
            else Variable.objects.none()
        )
        return context

    def test_func(self):
        return self.request.user.has_perm(Permission.TEAM_READ, self.get_object())
