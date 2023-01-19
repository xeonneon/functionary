from core.models.scheduled_task import ScheduledTask
from ui.views.view_base import PermissionedEnvironmentListView


class ScheduledTaskListView(PermissionedEnvironmentListView):
    model = ScheduledTask
    template_name = "core/scheduling_list.html"
