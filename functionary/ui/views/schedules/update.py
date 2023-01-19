from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, QueryDict
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from core.auth import Permission
from core.models import Environment, Function, ScheduledTask
from ui.forms import ScheduledTaskForm, TaskParameterForm
from ui.views.schedules.utils import get_crontab_schedule
from ui.views.view_base import PermissionedFormUpdateView


class ScheduledTaskUpdateView(PermissionedFormUpdateView):
    model = ScheduledTask
    form_class = ScheduledTaskForm
    template_name = "forms/schedules/scheduling_create_or_update.html"

    def get_success_url(self) -> str:
        return reverse("ui:schedule-list")

    def get_initial(self) -> dict:
        initial = super().get_initial()
        scheduled_task: ScheduledTask = self.get_object()
        crontab = scheduled_task.periodic_task.crontab
        initial["scheduled_minute"] = crontab.minute
        initial["scheduled_hour"] = crontab.hour
        initial["scheduled_day_of_week"] = crontab.day_of_week
        initial["scheduled_day_of_month"] = crontab.day_of_month
        initial["scheduled_month_of_year"] = crontab.month_of_year
        return initial

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        scheduled_task: ScheduledTask = self.get_object()
        context["update"] = True
        context["task_parameter_form"] = TaskParameterForm(
            function=scheduled_task.function, initial=scheduled_task.parameters
        )
        return context

    def get_form_kwargs(self) -> dict:
        kwargs = super().get_form_kwargs()
        environment = get_object_or_404(
            Environment, id=self.request.session.get("environment_id")
        )
        kwargs["environment"] = environment
        return kwargs

    def post(self, request: HttpRequest, **kwargs) -> HttpResponse:
        scheduled_task: ScheduledTask = self.get_object()
        data: QueryDict = request.POST.copy()
        data["environment"] = scheduled_task.environment
        data["function"] = get_object_or_404(Function, id=data["function"])
        task_parameter_form = TaskParameterForm(data["function"], data)

        # Run is valid to clean fields and generate errors if present
        if task_parameter_form.is_valid():
            pass

        data["parameters"] = task_parameter_form.cleaned_data
        form = ScheduledTaskForm(
            data=data, environment=scheduled_task.environment, instance=scheduled_task
        )
        if form.is_valid():
            form.save()
            scheduled_task.set_status(form.cleaned_data["status"])
            crontab_schedule = get_crontab_schedule(form.cleaned_data)
            scheduled_task.set_schedule(crontab_schedule)

            return HttpResponseRedirect(self.get_success_url())

        context = {
            "scheduledtask": scheduled_task,
            "update": True,
            "form": form,
            "task_parameter_form": task_parameter_form,
        }
        return render(
            request, "forms/schedules/scheduling_create_or_update.html", context
        )

    def test_func(self) -> bool:
        environment = get_object_or_404(
            Environment, id=self.request.session.get("environment_id")
        )
        return self.request.user.has_perm(Permission.TASK_UPDATE, environment)
