from json import dumps

from django.core.exceptions import ValidationError
from django.forms import Widget
from django.http import HttpResponseNotFound, QueryDict
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from django_celery_beat.validators import (
    crontab_validator,
    day_of_month_validator,
    day_of_week_validator,
    hour_validator,
    minute_validator,
    month_of_year_validator,
)

from core.models import Environment, Function, ScheduledTask
from ui.forms.tasks import _field_mapping, _get_param_type, _prepare_initial_value


def create_crontab_schedule(crontab_fields: dict) -> CrontabSchedule:
    """Creates and returns a crontab schedule

    If the submitted crontab schedule already exists, returns
    the existing crontab schedule. Otherwise, creates and
    returns a new crontab schedule.

    Args:
        crontab_fields: A dict that contains the crontab fields described in
            the SchdeuledTaskForm.

    Returns:
        CronTabSchedule: The new, or existing, crontab schedule
    """
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


def create_periodic_task(
    data: QueryDict, scheduled_task: ScheduledTask
) -> PeriodicTask:
    """Create a new periodic task

    Creates a new periodic task and assigns it to the given scheduled task.

    Args:
        data: A QueryDict that contains the ScheduledTaskForm data
        scheduled_task: The ScheduledTask object

    Returns:
        PeriodicTask: The newly created PeriodicTask
    """
    crontab_schedule = create_crontab_schedule(data)

    periodic_task = PeriodicTask.objects.create(
        crontab=crontab_schedule,
        name=data["name"],
        task="core.utils.tasking.run_scheduled_task",
        args=dumps([f"{scheduled_task.id}"]),
        enabled=False,
    )

    scheduled_task.periodic_task = periodic_task
    scheduled_task.save()

    return periodic_task


def get_function(function_id: str, env: Environment) -> Function:
    """Return Function given the function id and environment

    Simple helper function for retrieving the Function object given the
    function id string and environment object of the session. If the
    function is not available in the environment, or the function simply does
    not exist, return an HttpResponse

    Args:
        function_id: The Function objects id as a string
        env: The Environment object

    Returns either:
        Function: The function object if it exists within the environment
        HttpResponseNotFound: A HttpResponseNotFound response if the function does
            not exist at all or in the environment
    """
    try:
        if (
            function := Function.objects.filter(
                id=function_id, package__environment=env
            ).first()
        ) is None:
            return HttpResponseNotFound("Unknown Function submitted.")
        return function
    except ValidationError:
        return HttpResponseNotFound("Unknown Function submitted.")


def get_parameters(func: Function, parameter_values: dict = None) -> list[dict]:
    """Returns the parameters for a given function

    Returns a list of dictionaries containing all the parameters
    for a given function. If the parameter_values argument is passed,
    the default values of the parameters will be overriden.

    Args:
        func: The Function object whose parameters you want to get
        parameter_values: The optional dictionary that will override the
            parameter's default values

    Returns:
        parameters: A list of parameters. Each parameter is a dictionary.
    """

    parameters = []
    for param, value in func.schema["properties"].items():
        initial = value.get("default", None)
        req = initial is None
        param_type = _get_param_type(value)
        field_class, widget = _field_mapping.get(param_type, (None, None))

        if not field_class:
            raise ValueError(f"Unknown field type for {param}: {param_type}")

        initial_value = None
        if parameter_values is None:
            initial_value = _prepare_initial_value(param_type, initial)
        else:
            initial_value = parameter_values.get(param, initial)

        widget: Widget = field_class.widget()
        if param_type != "boolean":
            widget.attrs = {"class": "input is-medium is-fullwidth"}
        else:
            widget.attrs = {"class": "input is-medium", "type": "checkbox"}

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


def is_valid_scheduled_minute(field: str) -> bool:
    try:
        minute_validator(field)
        return True
    except Exception:
        return False


def is_valid_scheduled_hour(field: str) -> bool:
    try:
        hour_validator(field)
        return True
    except Exception:
        return False


def is_valid_scheduled_day_of_week(field: str) -> bool:
    try:
        day_of_week_validator(field)
        return True
    except Exception:
        return False


def is_valid_scheduled_day_of_month(field: str) -> bool:
    try:
        day_of_month_validator(field)
        return True
    except Exception:
        return False


def is_valid_scheduled_month_of_year(field: str) -> bool:
    try:
        month_of_year_validator(field)
        return True
    except Exception:
        return False


def update_status(status: str, scheduled_task: ScheduledTask) -> None:
    """Updates the status of the given scheduled task

    Given a new status string, update the given scheduled task's status
    to the new status, and perform that status's operation on the scheduled task.

    Args:
        status: A string that should be equivalent to any of the statuses defined
            in the ScheduledTask model
        scheduled_task: The ScheduledTask object whose status should be updated.

    Returns:
        None

    Raises:
        ValueError: If the given status is not a valid status, raises a ValueError.
    """
    match status:
        case ScheduledTask.ACTIVE:
            scheduled_task.activate()
        case ScheduledTask.PAUSED:
            scheduled_task.pause()
        case ScheduledTask.ARCHIVED:
            scheduled_task.archive()
        case _:
            raise ValueError("Unknown status given.")


def update_crontab(fields: dict, scheduled_task: ScheduledTask) -> None:
    """Helper function that updates a ScheduledTask's crontab schedule

    Args:
        fields: A dictionary containing the crontab fields
        scheduled_task: The ScheduledTask object whose crontab schedule should
            be updated

    Returns:
        None
    """
    crontab_schedule = create_crontab_schedule(fields)
    scheduled_task.periodic_task.crontab = crontab_schedule
    scheduled_task.periodic_task.save()
