from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponseRedirect, QueryDict
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import View

from core.auth import Permission
from core.models import Environment, EnvironmentUserRole, User
from ui.forms.environments import EnvUserRoleForm

from .utils import get_team_members


class EnvironmentCreateMemberView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request: HttpRequest, environment_id: str):
        environment = get_object_or_404(Environment, id=environment_id)

        form = EnvUserRoleForm()
        context = {
            "form": form,
            "environment_id": str(environment.id),
            "usernames": [user.username for user in User.objects.all()[:5]],
        }
        return render(request, "forms/environments/environment_add_user.html", context)

    def post(self, request: HttpRequest, environment_id: str):
        """Add user to the environment"""
        environment = get_object_or_404(Environment, id=environment_id)

        data: QueryDict = request.POST.copy()
        user = User.objects.filter(username=data["user"]).first()
        data["environment"] = environment
        data["user"] = user

        form = EnvUserRoleForm(data=data)
        if not form.is_valid():
            if user is None:
                form.add_error(
                    "user",
                    ValidationError("User not found.", code="invalid"),
                )

            context = {
                "form": form,
                "environment_id": str(environment.id),
                "usernames": [user.username for user in User.objects.all()[:5]],
            }
            return render(
                request, "forms/environments/environment_add_user.html", context
            )

        """
        This endpoint is for adding a user to the environment,
        not updating a user's role on the environment
        """
        if (
            _ := EnvironmentUserRole.objects.filter(
                environment=environment, user=user
            ).first()
        ) is not None or user in get_team_members(environment):
            form.add_error(
                "user",
                ValidationError(
                    "User already has a role in this environment.", code="invalid"
                ),
            )
            context = {"form": form, "environment_id": str(environment.id)}
            return render(
                request, "forms/environments/environment_add_user.html", context
            )

        _ = EnvironmentUserRole.objects.create(
            user=form.cleaned_data["user"],
            environment=form.cleaned_data["environment"],
            role=form.cleaned_data["role"],
        )
        return HttpResponseRedirect(
            reverse("ui:environment-detail", kwargs={"pk": environment.id})
        )

    def test_func(self) -> bool:
        environment = get_object_or_404(Environment, id=self.kwargs["environment_id"])
        return self.request.user.has_perm(Permission.ENVIRONMENT_UPDATE, environment)
