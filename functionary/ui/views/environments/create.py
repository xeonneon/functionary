from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, QueryDict
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import CreateView

from core.auth import Permission
from core.models import Environment, EnvironmentUserRole, TeamUserRole, User
from ui.forms.environments import EnvUserRoleForm
from ui.views.teams.utils import get_user_from_username

from .utils import get_user_from_userid


class EnvironmentCreateMemberView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = EnvironmentUserRole
    form_class = EnvUserRoleForm
    template_name = "forms/environmentuserrole_create_or_update.html"

    def get_success_url(self, **kwargs) -> str:
        environment = get_object_or_404(
            Environment, id=self.kwargs.get("environment_id")
        )
        return reverse("ui:environment-detail", kwargs={"pk": environment.id})

    def get(self, request: HttpRequest, environment_id: str, user_id: str = None):
        """
        Need to override Create's Get endpoint to handle the situation where
        the user wants to edit a Team member's role for an environment when they
        do not have an EnvironmentUserRole. This allows us to pass additional context
        to render the specific form.
        If the user is trying to edit the role of a Team user who does not have an
        Environment role, pass the user_id argument in the create URL, and render
        the create_user_from_team form. Otherwise, the user is trying to add a user
        who is not already part of the Team, so render the create_user form.
        """
        environment = get_object_or_404(Environment, id=environment_id)

        form = None
        if user_id:
            user = get_object_or_404(User, id=user_id)
            team_user_role = get_object_or_404(
                TeamUserRole, user=user, team=environment.team
            )
            form = EnvUserRoleForm(initial={"role": team_user_role.role})
        else:
            form = EnvUserRoleForm()

        context = {
            "form": form,
            "environment_id": str(environment.id),
            "create_user": True if not user_id else False,
            "create_user_from_team": True if user_id else False,
            "user_id": user_id,
            "username": user.username if user_id else "",
            "usernames": [user.username for user in User.objects.all()[:5]]
            if not user_id
            else [],
        }
        return render(
            request, "forms/environmentuserrole_create_or_update.html", context
        )

    def post(self, request: HttpRequest, environment_id: str, user_id: str = None):
        """
        Substitute user object for user field since the ModelForm clean method
        will invalidate the user field before calling the additional
        clean_<field> methods. This overriding should only be necessary for create
        endpoints, due to how the fuzzy find for users works.
        """
        data: QueryDict = request.POST.copy()
        user = get_user_from_username(data.get("user"))
        if not user:
            user = get_user_from_userid(user_id)

        data["user"] = user
        environment = get_object_or_404(Environment, id=environment_id)
        form = EnvUserRoleForm(data=data)

        """
        Need to pass additional context back to templates to handle which
        form will be rendered, so we need to handle the situations where a
        User already has a role on the Environment or the given
        user does not exist.
        This stems from the issue of needing to override the create view to
        handle updating the role of a Team member who might not have a role
        for the environment yet.
        """
        if (
            _ := EnvironmentUserRole.objects.filter(
                environment=environment, user=user
            ).first()
        ) is not None or not user:
            # Run cleaning methods to produce form errors
            _ = form.is_valid()

            context = {
                "form": form,
                "create_user": True,
                "environment_id": str(environment.id),
                "usernames": [user.username for user in User.objects.all()[:5]],
            }
            return render(
                request, "forms/environmentuserrole_create_or_update.html", context
            )

        """
        Replace the request.POST.data with our updated QueryDict. This is the only way
        to re-use the CreateView's POST method without needing to override the
        whole method.
        """
        request.POST = data
        return super().post(data, environment_id, user_id)

    def test_func(self) -> bool:
        environment = get_object_or_404(Environment, id=self.kwargs["environment_id"])
        return self.request.user.has_perm(Permission.ENVIRONMENT_UPDATE, environment)
