from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, QueryDict
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.views.generic import View
from thefuzz import process

from core.auth import Permission
from core.models import Environment, EnvironmentUserRole, User
from ui.forms.environments import EnvForm


class EnvironmentCreateMemberView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request: HttpRequest, environment_id: str):
        environment = get_object_or_404(Environment, id=environment_id)

        form = EnvForm()
        context = {
            "form": form,
            "environment_id": str(environment.id),
        }
        return render(
            request, "partials/environments/environment_add_user.html", context
        )

    def post(self, request: HttpRequest, environment_id: str):
        """Add user to the environment"""
        environment = get_object_or_404(Environment, id=environment_id)

        data: QueryDict = request.POST.copy()
        user = User.objects.filter(username=data["user"]).first()
        data["environment"] = environment
        data["user"] = user

        form = EnvForm(data=data)
        if not form.is_valid():
            if user is None:
                form.add_error(
                    "user",
                    ValidationError("User not found.", code="invalid"),
                )

            context = {"form": form, "environment_id": str(environment.id)}
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
        ) is not None:
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
            inherited=False,
        )
        return HttpResponseRedirect(
            reverse("ui:environment-detail", kwargs={"pk": environment.id})
        )

    def test_func(self) -> bool:
        environment = get_object_or_404(Environment, id=self.kwargs["environment_id"])
        return self.request.user.has_perm(Permission.ENVIRONMENT_UPDATE, environment)


@require_GET
@login_required
def get_users(request: HttpRequest) -> HttpResponse:
    username = request.GET.get("user")
    users = User.objects.all()
    results = process.extractBests(
        username, [user.username for user in users], score_cutoff=25
    )

    context = {"usernames": [result[0] for result in results]}
    return render(request, "partials/environments/user_list.html", context)
