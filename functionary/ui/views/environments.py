from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from core.auth import Permission
from core.models import Environment, Package, Variable


class EnvironmentListView(LoginRequiredMixin, ListView):
    model = Environment

    def get_queryset(self):
        """Sorts based on team name, then env name."""
        if self.request.user.is_superuser:
            return (
                super()
                .get_queryset()
                .select_related("team")
                .order_by("team__name", "name")
            )
        else:
            return self.request.user.environments().select_related("team")


class EnvironmentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Environment

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "team",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        env = self.get_object()
        context["packages"] = Package.objects.filter(environment=env)
        context["var_create"] = self.request.user.has_perm(
            Permission.VARIABLE_CREATE, env
        )
        context["var_update"] = self.request.user.has_perm(
            Permission.VARIABLE_UPDATE, env
        )
        context["var_delete"] = self.request.user.has_perm(
            Permission.VARIABLE_DELETE, env
        )
        context["variables"] = (
            env.vars
            if self.request.user.has_perm(Permission.VARIABLE_READ, env)
            else Variable.objects.none()
        )
        return context

    def test_func(self):
        return self.request.user.has_perm(
            Permission.ENVIRONMENT_READ, self.get_object()
        )


@require_POST
def set_environment_id(request):
    request.session["environment_id"] = request.POST["environment_id"]
    next = request.GET.get("next")
    if not next:
        next = "/ui/"
    return redirect(next)
