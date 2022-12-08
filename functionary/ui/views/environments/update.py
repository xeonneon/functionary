from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, QueryDict
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import View
from django.views.generic.base import TemplateView
from django_htmx import http

from core.auth import Permission
from core.models import Environment, EnvironmentUserRole, User
from ui.forms.environments import EnvForm

from .utils import get_user_env_role


class EnvironmentUpdateMemberView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request: HttpRequest, environment_id: str, user_id: str):
        environment = get_object_or_404(Environment, id=environment_id)
        user = get_object_or_404(User, id=user_id)
        env_user_role = get_user_env_role(user, environment)

        form = EnvForm(initial={"user": user, "role": env_user_role.role})
        context = {
            "form": form,
            "environment_id": str(environment.id),
            "user_id": str(user.id),
            "username": user.username,
        }
        return render(
            request, "partials/environments/environment_update_user.html", context
        )

    def post(self, request: HttpRequest, environment_id: str, user_id: str):
        """Update users role in the environment"""
        environment = get_object_or_404(Environment, id=environment_id)
        user = get_object_or_404(User, id=user_id)
        env_user_role = get_user_env_role(user, environment)

        data: QueryDict = request.POST.copy()
        data["environment"] = environment
        data["user"] = user

        form = EnvForm(data=data)
        if not form.is_valid():
            context = {
                "form": form,
                "environment_id": str(environment.id),
                "user_id": str(user.id),
                "username": user.username,
            }
            return (
                render(
                    request, "forms/environments/environment_update_user.html", context
                ),
            )

        # If user's role did not change
        if form.cleaned_data["role"] == env_user_role.role:
            return HttpResponseRedirect(
                reverse("ui:environment-detail", kwargs={"pk": environment.id})
            )

        _ = EnvironmentUserRole.objects.filter(
            user=form.cleaned_data["user"], environment=form.cleaned_data["environment"]
        ).update(role=form.cleaned_data["role"])

        return HttpResponseRedirect(
            reverse("ui:environment-detail", kwargs={"pk": environment.id})
        )

    def test_func(self) -> bool:
        environment = get_object_or_404(Environment, id=self.kwargs["environment_id"])
        return self.request.user.has_perm(Permission.ENVIRONMENT_UPDATE, environment)


class EnvironmentSelectView(LoginRequiredMixin, TemplateView):
    environments = {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["environments"] = self.environments
        return context

    def post(self, request):
        pk = request.POST["environment_id"]
        get_object_or_404(Environment, id=pk)

        request.session["environment_id"] = pk
        next = request.POST.get("next")
        if not next:
            next = "/ui/"
        return http.trigger_client_event(HttpResponse(""), "reloadData")

    def get(self, request):
        if self.request.user.is_superuser:
            envs = (
                Environment.objects.select_related("team")
                .all()
                .order_by("team__name", "name")
            )
        else:
            envs = self.request.user.environments.select_related("team").order_by(
                "team__name", "name"
            )

        self.environments = {}
        for env in envs:
            self.environments.setdefault(env.team.name, []).append(env)

        ctx = self.get_context_data()
        ctx["next"] = request.GET["next"]
        return render(request, "forms/environment_selector.html", ctx)
