from django.core.exceptions import PermissionDenied
from django.forms import Widget
from django_unicorn.components import QuerySetType, UnicornView

from core.auth import Permission
from core.models import Function, Package

from ..forms.forms import (
    ScheduledTaskForm,
    _field_mapping,
    _get_param_type,
    _prepare_initial_value,
)


class ScheduledTaskFormView(UnicornView):
    form: ScheduledTaskForm = None
    selected_function: Function = None
    available_functions: QuerySetType[Function] = None
    minute: str = "*"
    hour: str = "*"
    day_of_week: str = "*"
    day_of_month: str = "*"
    month_of_year: str = "*"
    parameters: list[dict] = [{}]

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.selected_function = self.get_first_available_function()
        self.available_functions = self.get_available_functions()
        self.parameters = self.get_parameters()
        self.form = kwargs.get("form")

    def hydrate(self):
        env = self.request.session.get("environment_id")
        if not self.request.user.has_perm(Permission.TASK_READ, env):
            raise PermissionDenied

    def mount(self):
        self.selected_function = self.get_first_available_function()
        self.available_functions = self.get_available_functions()
        self.parameters = self.get_parameters()
        print(f"Default function: {self.selected_function}")

    def update_displayed_function(self, function):
        pass

    def get_first_available_function(self):
        if (available_functions := self.get_available_functions().first()) is None:
            raise Exception("No available functions")
        return available_functions

    def get_available_functions(self):
        env = self.request.session.get("environment_id")
        available_packages = Package.objects.filter(environment=env)
        return Function.objects.filter(package__in=available_packages)

    def get_parameters(self):
        parameters = []
        for param, value in self.selected_function.schema["properties"].items():
            initial = value.get("default", None)
            req = initial is None
            param_type = _get_param_type(value)
            field_class, widget = _field_mapping.get(param_type, (None, None))

            if not field_class:
                raise ValueError(f"Unknown field type for {param}: {param_type}")

            initial_value = _prepare_initial_value(param_type, initial)
            widget: Widget = field_class.widget()
            widget.attrs = {"class": "input is-medium is-fullwidth"}
            parameter = {
                "label": value["title"],
                "label_suffix": param_type,
                "initial": initial_value,
                "required": req,
                "help_text": value.get("description", None),
                "widget": widget.render(value["title"], initial_value),
            }

            parameters.append(parameter)

        return parameters

    class Meta:
        javascript_exclude = (
            "form",
            "selected_function",
        )
