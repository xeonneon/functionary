from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.detail import DetailView

from core.auth import Permission
from core.models import Environment, Package, Variable

from .utils import get_users


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
        env_members = get_users(env)

        context["packages"] = Package.objects.filter(environment=env)
        context["environment_create_perm"] = (
            True
            if (self.request.user.has_perm(Permission.ENVIRONMENT_UPDATE, env))
            else False
        )
        context["users"] = env_members
        context["environment_id"] = str(env.id)
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
