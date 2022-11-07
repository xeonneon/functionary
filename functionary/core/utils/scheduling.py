from json import dumps

from django.http import QueryDict
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from django_celery_beat.validators import crontab_validator

from core.models import ScheduledTask


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


def create_periodic_task(
    data: QueryDict, scheduled_task: ScheduledTask
) -> PeriodicTask:
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
