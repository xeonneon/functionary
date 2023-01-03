from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView

from core.models import Team


class TeamListView(LoginRequiredMixin, ListView):
    model = Team

    def get_queryset(self):
        """Sorts based on team name, then env name."""
        if self.request.user.is_superuser:
            return super().get_queryset().order_by("name")
        else:
            return Team.objects.filter(user_roles__user=self.request.user)
