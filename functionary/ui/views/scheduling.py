from datetime import date, datetime
from json import dumps
from typing import Any, Callable

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
    QueryDict,
)
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from django_celery_beat.validators import crontab_validator

from core.auth import Permission
from core.models import Environment, Function, ScheduledTask

from ..forms.forms import ScheduledTaskForm, get_available_functions
from .view_base import PermissionedEnvironmentListView, PermissionedFormView


class ScheduledTaskListView(PermissionedEnvironmentListView):
    model = ScheduledTask
    template_name = "core/scheduled_task_list.html"


class ScheduledTaskFormView(PermissionedFormView):
    form_class = ScheduledTaskForm
    success_url = "/scheduled_tasks"
    template_name = "core/scheduled_task_form.html"

    def get(self, *args, **kwargs):
        env = Environment.objects.get(id=self.request.session.get("environment_id"))
        if not len(get_available_functions(env)):
            messages.warning(self.request, "No available functions to schedule in current environment.")
            return redirect("ui:scheduled-tasks")
        return super().get(*args, **kwargs)


@require_POST
@login_required
def execute_scheduled_task(request) -> HttpResponse:
    func = None
    form = None

    env = Environment.objects.get(id=request.session.get("environment_id"))
    if not request.user.has_perm(Permission.TASK_CREATE, env):
        return HttpResponseForbidden()

    print(f"Post request: {request.POST}")

    func = get_function(request.POST["function"], env)
    data: QueryDict = request.POST.copy()
    data["function"] = func
    data["environment"] = env
    data["parameters"] = get_function_parameters(func, request.POST)
    form = ScheduledTaskForm(data=data)

    if form.is_valid():
        print(f"Form data: {form.cleaned_data}")

        scheduled_task = ScheduledTask.objects.create(
            name=form.cleaned_data["name"],
            environment=form.cleaned_data["environment"],
            function=form.cleaned_data["function"],
            parameters=form.cleaned_data["parameters"],
            creator=request.user,
        )

        _ = create_periodic_task(form.cleaned_data, scheduled_task)
        return HttpResponseRedirect(reverse("ui:scheduled-tasks"))

    print(f"Failed: {form.data}")
    return HttpResponse(f"Error {form.errors}")


def get_function(function_name: str, env: Environment) -> Function:
    available_functions = get_available_functions(env)
    if (function := available_functions.filter(name=function_name).first()) is None:
        raise Exception("Function does not exist")
    return function


def get_function_parameters(func: Function, data: QueryDict) -> dict:
    parameter_fields = {}
    for param, value in func.schema["properties"].items():
        if (param_value := data.get(param)) is None:
            raise ValueError(f"Missing argument: {param}")
        param_value = cast_parameter_type(param_value, value["type"])
        parameter_fields[param] = param_value
    print(f"Parameter fields: {parameter_fields}")
    return dumps(parameter_fields)


def cast_parameter_type(param: str, cast_type: str):
    match cast_type:
        case "integer":
            return cast_to_type(param, int)
        case "string":
            return cast_to_type(param, str)
        case "text":
            return cast_to_type(param, str)
        case "number":
            return cast_to_type(param, float)
        case "boolean":
            return cast_to_type(param, bool)
        case "date":
            return cast_to_type(param, date)
        case "date-time":
            return cast_to_type(param, datetime)
        case "json":
            return cast_to_type(param, dict)
        case _:
            print("Found no matching type")
            raise Exception("No matching value")


def cast_to_type(param: str, target_type: Callable) -> Any:
    try:
        param = target_type(param)
        return param
    except ValueError as err:
        raise ValueError(f"Invalid value for paramter type: {err}")


def create_crontab_schedule(crontab_fields: dict) -> CrontabSchedule:
    minute = crontab_fields["scheduled_minute"]
    hour = crontab_fields["scheduled_hour"]
    day_of_week = crontab_fields["scheduled_day_of_week"]
    day_of_month = crontab_fields["scheduled_day_of_month"]
    month_of_year = crontab_fields["scheduled_month_of_year"]
    crontab_str = f"{minute} {hour} {day_of_month} {month_of_year} {day_of_week}"
    try:
        crontab_validator(crontab_str)
        crontab_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=minute,
            hour=hour,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            month_of_year=month_of_year,
        )
        return crontab_schedule
    except ValueError as err:
        print(f"Invalid Crontab. {err}")
        raise ValueError(err)


def create_periodic_task(data: QueryDict, scheduled_task: ScheduledTask) -> PeriodicTask:
    crontab_schedule = create_crontab_schedule(data)

    periodic_task = PeriodicTask.objects.create(
        crontab=crontab_schedule,
        name=data["name"],
        task="core.utils.tasking.run_scheduled_task",
        kwargs=dumps({
                "scheduled_task_id": f"{scheduled_task.id}"}
            ),
        enabled=True,
    )

    scheduled_task.periodic_task = periodic_task
    scheduled_task.save()

    return periodic_task
