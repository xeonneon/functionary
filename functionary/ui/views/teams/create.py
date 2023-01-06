from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse, QueryDict
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.views.generic import CreateView
from rapidfuzz import process

from core.auth import Permission
from core.models import Team, TeamUserRole, User
from ui.forms.teams import TeamUserRoleForm
from ui.views.teams.utils import get_user_from_username


class TeamCreateMemberView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = TeamUserRole
    form_class = TeamUserRoleForm
    template_name = "forms/teamuserrole_create_or_update.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, id=self.kwargs.get("team_id"))

        # Use string of id field if it is a UUID
        context["team_id"] = str(team.id)
        context["create_user"] = True
        context["usernames"] = User.objects.all()[:5]
        return context

    def get_success_url(self, **kwargs) -> str:
        team = get_object_or_404(Team, id=self.kwargs.get("team_id"))
        return reverse("ui:team-detail", kwargs={"pk": team.id})

    def post(self, request: HttpRequest, team_id: str):
        """
        Substitute user object for user field since the ModelForm clean method
        will invalidate the user field before calling the additional
        clean_<field> methods. This overriding should only be necessary for create
        endpoints, due to how the fuzzy find for users works.
        """
        data: QueryDict = request.POST.copy()
        data["user"] = get_user_from_username(data.get("user"))

        """
        Replace the request.POST.data with our updated QueryDict. This is the only way
        to re-use the CreateView's POST method without needing to override the
        whole method.
        """
        request.POST = data
        return super().post(data, team_id)

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
