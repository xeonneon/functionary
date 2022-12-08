from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView

from core.models import Team, TeamUserRole


class TeamListView(LoginRequiredMixin, ListView):
    model = Team

    def get_queryset(self):
        """Sorts based on team name, then env name."""
        if self.request.user.is_superuser:
            return super().get_queryset().order_by("name")
        else:
            teams = TeamUserRole.objects.filter(user=self.request.user).values(
                "team_id"
            )
            return Team.objects.filter(id__in=[team["team_id"] for team in teams])
