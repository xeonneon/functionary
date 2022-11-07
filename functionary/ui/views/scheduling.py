from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
    QueryDict,
)
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.auth import Permission
from core.models import Environment, Function, ScheduledTask
from core.utils.scheduling import create_periodic_task

from ..forms.forms import ScheduledTaskForm, TaskParameterForm, get_available_functions
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
            messages.warning(
                self.request,
                "No available functions to schedule in current environment.",
            )
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
    function_params_form = TaskParameterForm(func, data)

    # Validate function parameters are valid first
    if function_params_form.is_valid():
        data["parameters"] = function_params_form.cleaned_data
    else:
        return HttpResponse(f"Error {form.errors}")

    form = ScheduledTaskForm(data=data)
    if form.is_valid() and function_params_form.is_valid():
        print(f"Form data: {form.cleaned_data}")
        print(f"Param form cleaned data: {function_params_form.cleaned_data}")

        scheduled_task = ScheduledTask.objects.create(
            name=form.cleaned_data["name"],
            environment=form.cleaned_data["environment"],
            function=form.cleaned_data["function"],
            parameters=function_params_form.cleaned_data,
            creator=request.user,
        )

        scheduled_task.periodic_task = create_periodic_task(
            form.cleaned_data, scheduled_task
        )
        scheduled_task.activate()
        return HttpResponseRedirect(reverse("ui:scheduled-tasks"))

    print(f"Failed: {form.errors}")
    context = {"form": ScheduledTaskForm(), "errors": form.errors}
    return render(request, "core/scheduled_task_form.html", context)


def get_function(function_name: str, env: Environment) -> Function:
    available_functions = get_available_functions(env)
    if (function := available_functions.filter(name=function_name).first()) is None:
        raise Exception("Function does not exist")
    return function
