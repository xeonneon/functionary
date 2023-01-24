from core.models import Task
from core.models.scheduled_task import ScheduledTask
from ui.views.view_base import PermissionedEnvironmentDetailView


class ScheduledTaskDetailView(PermissionedEnvironmentDetailView):
    model = ScheduledTask
    template_name = "core/scheduling_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scheduledtask: ScheduledTask = context["scheduledtask"]
        history = Task.objects.filter(scheduled_task=scheduledtask).order_by(
            "-created_at"
        )[:10]
        context["history"] = history
        return context
