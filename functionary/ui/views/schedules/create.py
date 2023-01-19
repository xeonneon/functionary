from django.contrib import messages
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.auth import Permission
from core.models import Environment, Function, ScheduledTask
from ui.forms import ScheduledTaskForm, TaskParameterForm
from ui.views.view_base import PermissionedFormCreateView

from .utils import get_crontab_schedule


class ScheduledTaskCreateView(PermissionedFormCreateView):
    model = ScheduledTask
    form_class = ScheduledTaskForm
    template_name = "forms/schedules/scheduling_create_or_update.html"

    def get_success_url(self) -> str:
        return reverse("ui:schedule-list")

    def get_form_kwargs(self) -> dict:
        kwargs = super().get_form_kwargs()
        environment = get_object_or_404(
            Environment, id=self.request.session.get("environment_id")
        )
        kwargs["environment"] = environment
        return kwargs

    def get(self, *args, **kwargs):
        environment_id = self.request.session.get("environment_id")
        if not Function.objects.filter(package__environment=environment_id).exists():
            messages.warning(
                self.request,
                "No available functions to schedule in current environment.",
            )
            return redirect("ui:schedule-list")
        return super().get(*args, **kwargs)

    def post(self, request: HttpRequest) -> HttpResponse:
        data = request.POST.copy()
        data["environment"] = get_object_or_404(
            Environment, id=self.request.session.get("environment_id")
        )
        data["function"] = get_object_or_404(Function, id=data["function"])
        data["status"] = ScheduledTask.PENDING

        task_parameter_form = TaskParameterForm(data["function"], data)

        # Run is valid to clean fields and generate errors if present
        if task_parameter_form.is_valid():
            pass

        data["parameters"] = task_parameter_form.cleaned_data
        scheduled_task_form = ScheduledTaskForm(
            data=data, environment=data["environment"], is_create=True
        )
        if scheduled_task_form.is_valid():
            _create_scheduled_task(
                request,
                scheduled_task_form.cleaned_data,
                task_parameter_form.cleaned_data,
            )
            return HttpResponseRedirect(self.get_success_url())

        context = {
            "form": scheduled_task_form,
            "task_parameter_form": task_parameter_form,
        }
        return render(
            request, "forms/schedules/scheduling_create_or_update.html", context
        )

    def test_func(self) -> bool:
        environment = get_object_or_404(
            Environment, id=self.request.session.get("environment_id")
        )
        return self.request.user.has_perm(Permission.TASK_CREATE, environment)


def _create_scheduled_task(
    request: HttpRequest, schedule_form_data: dict, task_params: dict
):
    """Helper function for creating scheduled task"""
    with transaction.atomic():
        scheduled_task = ScheduledTask.objects.create(
            name=schedule_form_data["name"],
            environment=schedule_form_data["environment"],
            description=schedule_form_data["description"],
            function=schedule_form_data["function"],
            parameters=task_params,
            creator=request.user,
        )
        crontab_schedule = get_crontab_schedule(schedule_form_data)
        scheduled_task.set_schedule(crontab_schedule)
        scheduled_task.activate()
