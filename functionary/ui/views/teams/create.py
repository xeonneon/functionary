from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, QueryDict
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.views.generic import View
from rapidfuzz import process

from core.auth import Permission
from core.models import Team, TeamUserRole, User
from ui.forms.teams import TeamUserRoleForm


class TeamCreateMemberView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request: HttpRequest, team_id: str):
        team = get_object_or_404(Team, id=team_id)

        form = TeamUserRoleForm()
        context = {
            "form": form,
            "team_id": str(team.id),
            "create_user": True,
            "usernames": [user.username for user in User.objects.all()[:5]],
        }
        return render(request, "forms/teamuserrole_create_or_update.html", context)

    def post(self, request: HttpRequest, team_id: str):
        """Add user to team"""
        team = get_object_or_404(Team, id=team_id)

        data: QueryDict = request.POST.copy()
        user = User.objects.filter(username=data["user"]).first()
        data["team"] = team
        data["user"] = user

        form = TeamUserRoleForm(data=data)

        """
        This endpoint is for adding a user to the team,
        not updating a user's role on the team
        """
        if (_ := TeamUserRole.objects.filter(team=team, user=user).first()) is not None:
            form.add_error(
                "user",
                ValidationError(
                    "User already has a role on this team.", code="invalid"
                ),
            )
            context = {
                "form": form,
                "team_id": str(team.id),
                "create_user": True,
                "usernames": [user.username for user in User.objects.all()[:5]],
            }
            return render(request, "forms/teamuserrole_create_or_update.html", context)

        if not form.is_valid():
            if user is None:
                form.add_error(
                    "user",
                    ValidationError("User not found.", code="invalid"),
                )

            context = {
                "form": form,
                "team_id": str(team.id),
                "create_user": True,
                "usernames": [user.username for user in User.objects.all()[:5]],
            }
            return render(request, "forms/teamuserrole_create_or_update.html", context)

        form.save()

        return HttpResponseRedirect(reverse("ui:team-detail", kwargs={"pk": team.id}))

    def test_func(self) -> bool:
        team = get_object_or_404(Team, id=self.kwargs["team_id"])
        return self.request.user.has_perm(Permission.TEAM_UPDATE, team)


@require_GET
@login_required
def get_users(request: HttpRequest) -> HttpResponse:
    username = request.GET.get("user")
    users = User.objects.all()

    if username == "":
        context = {"usernames": [user.username for user in users[:5]]}
        return render(request, "partials/teams/user_list.html", context)

    results = process.extract(
        username, [user.username for user in users], score_cutoff=50
    )

    context = {"usernames": [result[0] for result in results]}
    return render(request, "partials/teams/user_list.html", context)
