from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView

from core.models import Environment


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
