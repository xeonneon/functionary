import json

from django.db.models.query import QuerySet
from django.forms import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    FloatField,
    Form,
    IntegerField,
    JSONField,
    ModelForm,
    Textarea,
    ValidationError,
)
from django.forms.widgets import DateInput, DateTimeInput

from core.models import Environment, Function, ScheduledTask


class HTMLDateInput(DateInput):
    input_type = "date"


class HTMLDateTimeInput(DateTimeInput):
    input_type = "datetime-local"


_field_mapping = {
    "integer": (IntegerField, None),
    "string": (CharField, None),
    "text": (CharField, Textarea),
    "number": (FloatField, None),
    "boolean": (BooleanField, None),
    "date": (DateField, HTMLDateInput),
    "date-time": (
        DateTimeField,
        HTMLDateTimeInput,
    ),
    "json": (JSONField, Textarea),
}

_transform_initial_mapping = {"json": json.loads}


def _get_param_type(param_dict):
    """Finds the type of the parameter from the definition in the schema.

    Pydantic maps to python types correctly, but we want to use the actual
    schema type for input purposes. If there is a format in the param_dict,
    the input field has a definition of what type it is. If there is an anyOf,
    inspect it and try find out what type it should be. Otherwise, return the
    value of 'type' in param_dict.
    """
    keys = param_dict.keys()

    # pydantic hides the date type in the format field
    if "format" in keys:
        return param_dict["format"]
    # json and text get mapped to TypeVars to preserve the distinction vs string
    elif "anyOf" in keys:
        return (
            "json"
            if any(
                param_types.get("format", None) == "json-string"
                for param_types in param_dict["anyOf"]
            )
            else "text"
        )
    else:
        return param_dict["type"]


def _prepare_initial_value(param_type, initial):
    """Convert the initial value to the appropriate type.

    This function will massage the initial value as needed into the type
    required for the parameter field. Currently, JSON types need to be
    converted from a string into an object, otherwise display issues
    occur in the form.
    """
    if initial:
        if param_type in _transform_initial_mapping:
            return _transform_initial_mapping[param_type](initial)
        else:
            return initial
    return None


def get_available_functions(env: Environment) -> QuerySet[Function]:
    return Function.objects.filter(package__environment=env)


class TaskParameterForm(Form):
    template_name = "forms/task_parameters.html"

    def __init__(self, function: Function, data=None):
        super().__init__(data)

        for param, value in function.schema["properties"].items():
            initial = value.get("default", None)
            req = initial is None
            param_type = _get_param_type(value)
            field_class, widget = _field_mapping.get(param_type, (None, None))

            if not field_class:
                raise ValueError(f"Unknown field type for {param}: {param_type}")

            kwargs = {
                "label": value["title"],
                "label_suffix": param_type,
                "initial": _prepare_initial_value(param_type, initial),
                "required": req,
                "help_text": value.get("description", None),
            }

            if widget:
                kwargs["widget"] = widget

            field = field_class(**kwargs)

            # Style all inputfields except the checkbox with the "input" class
            if param_type != "boolean":
                field.widget.attrs.update({"class": "input"})
            self.fields[param] = field


class ScheduledTaskForm(ModelForm):
    scheduled_minute = CharField(max_length=60 * 4, label="Minute")
    scheduled_hour = CharField(max_length=24 * 4, label="Hour")
    scheduled_day_of_week = CharField(max_length=64, label="Day of Week")
    scheduled_day_of_month = CharField(max_length=31 * 4, label="Day of Month")
    scheduled_month_of_year = CharField(max_length=64, label="Month of Year")

    class Meta:
        model = ScheduledTask
        fields = ["name", "function", "parameters", "environment"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_field_classes()

    def clean(self):
        cleaned_data = super().clean()
        available_functions = get_available_functions(cleaned_data["environment"])
        if cleaned_data["function"] not in available_functions:
            raise ValidationError("Unknown function was provided.", code="invalid")

        print(f"Cleaned data: {cleaned_data}")
        return cleaned_data

    def _setup_field_classes(self):
        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": "input"})

        self.fields["name"].widget.attrs.update(
            {"class": "input is-medium is-fullwidth"}
        )
        self.fields["scheduled_minute"].widget.attrs.update(
            {"unicorn:model": "minute", "unicorn:partial": "id_scheduled_minute"}
        )
        self.fields["scheduled_hour"].widget.attrs.update(
            {"unicorn:model": "hour", "unicorn:partial": "id_scheduled_hour"}
        )
        self.fields["scheduled_day_of_week"].widget.attrs.update(
            {
                "unicorn:model": "day_of_week",
                "unicorn:partial": "id_scheduled_day_of_week",
            }
        )
        self.fields["scheduled_day_of_month"].widget.attrs.update(
            {
                "unicorn:model": "day_of_month",
                "unicorn:partial": "id_scheduled_day_of_month",
            }
        )
        self.fields["scheduled_month_of_year"].widget.attrs.update(
            {
                "unicorn:model": "month_of_year",
                "unicorn:partial": "id_scheduled_month_of_year",
            }
        )
