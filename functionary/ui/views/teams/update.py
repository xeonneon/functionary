from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponseRedirect, QueryDict
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import View

from core.auth import Permission
from core.models import Team, TeamUserRole, User
from ui.forms.teams import TeamUserRoleForm


class TeamUpdateMemberView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request: HttpRequest, team_id: str, user_id: str):
        team = get_object_or_404(Team, id=team_id)
        user = get_object_or_404(User, id=user_id)
        team_user_role = TeamUserRole.objects.get(user=user, team=team)

        form = TeamUserRoleForm(initial={"user": user, "role": team_user_role.role})
        context = {
            "form": form,
            "team_id": str(team.id),
            "user_id": str(user.id),
            "username": user.username,
        }
        return render(request, "forms/teams/team_update_user.html", context)

    def post(self, request: HttpRequest, team_id: str, user_id: str):
        team = get_object_or_404(Team, id=team_id)
        user = get_object_or_404(User, id=user_id)

        data: QueryDict = request.POST.copy()
        data["team"] = team
        data["user"] = user

        form = TeamUserRoleForm(data=data)
        if not form.is_valid():
            context = {
                "form": form,
                "team_id": str(team.id),
                "user_id": str(user.id),
                "username": user.username,
            }
            return (render(request, "forms/teams/team_update_user.html", context),)

        _ = TeamUserRole.objects.filter(
            user=form.cleaned_data["user"], team=form.cleaned_data["team"]
        ).update(role=form.cleaned_data["role"])

        return HttpResponseRedirect(reverse("ui:team-detail", kwargs={"pk": team.id}))

    def test_func(self) -> bool:
        team = get_object_or_404(Team, id=self.kwargs["team_id"])
        return self.request.user.has_perm(Permission.TEAM_UPDATE, team)
