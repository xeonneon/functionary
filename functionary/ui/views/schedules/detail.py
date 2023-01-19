from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from core.auth import Permission
from core.models import Task
from core.models.environment import Environment
from core.models.function import Function
from core.models.scheduled_task import ScheduledTask
from ui.forms.tasks import TaskParameterForm
from ui.views.view_base import PermissionedEnvironmentDetailView

PAGINATION_AMOUNT = 15


class ScheduledTaskDetailView(PermissionedEnvironmentDetailView):
    model = ScheduledTask
    template_name = "core/scheduling_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scheduledtask: ScheduledTask = self.get_object()
        history = Task.objects.filter(scheduled_task=scheduledtask).order_by(
            "-created_at"
        )
        paginator = Paginator(history, PAGINATION_AMOUNT)
        page_obj = paginator.get_page(self.request.GET.get("page"))
        context["paginator"] = paginator
        context["page_obj"] = page_obj
        return context


# TODO: Move this endpoint somewhere else if it is going to be used by other views
@require_GET
@login_required
def function_parameters(request: HttpRequest) -> HttpResponse:
    """Used to lazy load a function's parameters as a partial.

    Always expects a 'function_id' parameter in the request, which is the ID of the
    function object whose parameters should be rendered.
    """
    env = Environment.objects.get(id=request.session.get("environment_id"))

    if not request.user.has_perm(Permission.ENVIRONMENT_READ, env):
        return HttpResponseForbidden()

    if (function_id := request.GET.get("function", None)) in ["", None]:
        return HttpResponse("No function selected.")

    function = get_object_or_404(Function, id=function_id, package__environment=env)

    # If the request includes the scheduled_task_id, substitute the default
    # widget values for the existing ScheduledTask parameters.
    existing_parameters = None
    if (scheduled_task_id := request.GET.get("scheduled_task_id", None)) is not None:
        scheduled_task = ScheduledTask.objects.get(id=scheduled_task_id)
        existing_parameters = scheduled_task.parameters

    form = TaskParameterForm(function=function, initial=existing_parameters)
    return render(request, form.template_name, {"form": form})
