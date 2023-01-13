from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic.base import TemplateView
from django.views.generic.edit import UpdateView
from django_htmx import http

from core.auth import Permission
from core.models import Environment, EnvironmentUserRole
from ui.forms.environments import EnvironmentUserRoleForm

from .utils import get_user_role


class EnvironmentUserRoleUpdateView(
    LoginRequiredMixin, UserPassesTestMixin, UpdateView
):
    model = EnvironmentUserRole
    form_class = EnvironmentUserRoleForm
    template_name = "forms/environment/environmentuserrole_update.html"

    def get_success_url(self) -> str:
        return reverse(
            "ui:environment-detail", kwargs={"pk": self.kwargs.get("environment_id")}
        )

    def get_initial(self) -> dict:
        environment_user_role: EnvironmentUserRole = self.get_object()
        initial = super().get_initial()
        role, _ = get_user_role(
            environment_user_role.user, environment_user_role.environment
        )
        initial["role"] = role.role if role else initial["role"]
        return initial

    def test_func(self) -> bool:
        environment = get_object_or_404(Environment, id=self.kwargs["environment_id"])
        return self.request.user.has_perm(Permission.ENVIRONMENT_UPDATE, environment)


class EnvironmentSelectView(LoginRequiredMixin, TemplateView):
    environments = {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["environments"] = self.environments
        return context

    def post(self, request: HttpRequest):
        pk = request.POST["environment_id"]
        get_object_or_404(Environment, id=pk)

        request.session["environment_id"] = pk
        next = request.POST.get("next")
        if not next:
            next = "/ui/"
        return http.trigger_client_event(HttpResponse(""), "reloadData")

    def get(self, request: HttpRequest):
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
