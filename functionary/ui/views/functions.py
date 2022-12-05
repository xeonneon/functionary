from django.contrib.auth.decorators import login_required
from django.core.exceptions import BadRequest, ValidationError
from django.db.models import QuerySet
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseRedirect,
)
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_POST
from thefuzz import fuzz, process

from core.auth import Permission
from core.models import Environment, Function, Task

from ..forms.tasks import TaskParameterForm
from .view_base import (
    PermissionedEnvironmentDetailView,
    PermissionedEnvironmentListView,
)


class FunctionListView(PermissionedEnvironmentListView):
    model = Function
    environment_through_field = "package"
    queryset = Function.objects.select_related("package").all()
    order_by_fields = ["package__name", "name"]


class FunctionDetailView(PermissionedEnvironmentDetailView):
    model = Function
    environment_through_field = "package"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "package", "package__environment", "package__environment__team"
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        function = self.object
        env = function.package.environment

        missing_variables = []
        if function.variables:
            all_vars = list(env.variables.values_list("name", flat=True))
            missing_variables = [
                var for var in function.variables if var not in all_vars
            ]
        context["missing_variables"] = missing_variables
        if self.request.user.has_perm(Permission.TASK_CREATE, env):
            form = TaskParameterForm(function)

            context["form"] = form.render("forms/task_parameters.html")
        return context


@require_POST
@login_required
def execute(request) -> HttpResponse:
    func = None
    form = None

    env = Environment.objects.get(id=request.session.get("environment_id"))
    if request.user.has_perm(Permission.TASK_CREATE, env):
        func = Function.objects.get(id=request.POST["function_id"])
        form = TaskParameterForm(func, request.POST)

        if form.is_valid():
            # Create the new Task, the validated parameters are in form.cleaned_data
            task = Task.objects.create(
                environment=env,
                creator=request.user,
                function=func,
                parameters=form.cleaned_data,
                return_type=func.return_type,
            )

            # redirect to a new URL:
            return HttpResponseRedirect(reverse("ui:task-detail", args=(task.id,)))
        args = {"form": form, "function": func}
        return render(request, "core/function_detail.html", args)

    return HttpResponseForbidden()


@require_POST
@login_required
def search_for_functions(request: HttpRequest) -> HttpResponse:
    env = Environment.objects.get(id=request.session.get("environment_id"))
    if not request.user.has_perm(Permission.ENVIRONMENT_READ, env):
        return HttpResponseForbidden()

    if (search := request.POST.get("search", None)) is None:
        return HttpResponse("")

    functions = Function.objects.filter(package__environment=env).order_by("name")

    if search == "":
        context = {"object_list": functions}
        return render(request, "partials/function_search_results.html", context)

    results = process.extractBests(
        search,
        [func.name for func in functions] + [func.display_name for func in functions],
        score_cutoff=25,
    )
    available_functions = filter_out_result_functions(functions, results)

    context = {"object_list": available_functions}
    return render(request, "partials/function_search_results.html", context)


def filter_out_result_functions(
    functions: QuerySet[Function], results: list[(str, int)]
) -> list[Function]:
    function_choices = []
    function_names = [func.name for func in functions]
    for result in results:
        if result[0] in function_names:
            function_choices.append(functions.get(name=result[0]))
    return function_choices
