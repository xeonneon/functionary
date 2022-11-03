import logging
from uuid import UUID

from celery.utils.log import get_task_logger
from django.conf import settings
from django.http import QueryDict
from django_celery_beat.models import PeriodicTask

from core.celery import app
from core.models import ScheduledTask, Task, TaskLog, TaskResult
from core.utils.messaging import get_route, send_message

logger = get_task_logger(__name__)
logger.setLevel(getattr(logging, settings.LOG_LEVEL))


def _generate_task_message(task: Task) -> dict:
    """Generates tasking message from the provided Task"""
    return {
        "id": str(task.id),
        "package": task.function.package.full_image_name,
        "function": task.function.name,
        "function_parameters": task.parameters,
    }


@app.task(
    default_retry_delay=30,
    retry_kwargs={
        "max_retries": 3,
    },
    autoretry_for=(Exception,),
)
def publish_task(task_id: UUID) -> None:
    """Publish the tasking message to the message broker so that it can be received
    and executed by a runner.

    Args:
        task_id: ID of the task to be executed
    """
    logger.debug(f"Publishing message for Task: {task_id}")

    task = Task.objects.select_related("function", "function__package").get(id=task_id)

    exchange, routing_key = get_route(task)
    send_message(exchange, routing_key, "TASK_PACKAGE", _generate_task_message(task))


@app.task()
def record_task_result(task_result_message: dict) -> None:
    """Parses the task result message and generates a TaskResult entry for it

    Args:
        task_result_message: The message body from a TASK_RESULT message.
    """
    task_id = task_result_message["task_id"]
    status = task_result_message["status"]
    output = task_result_message["output"]
    result = task_result_message["result"]

    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        logger.error("Unable to record results for task %s: task not found", task_id)
        return

    TaskLog.objects.create(task=task, log=output)
    TaskResult.objects.create(task=task, result=result)

    # TODO: This status determination feels like it belongs in the runner. This should
    #       be reworked so that there are explicitly known statuses that could come
    #       back from the runner, rather than passing through the command exit status
    #       as is happening now.
    task.status = "COMPLETE" if status == 0 else "ERROR"
    task.save()


@app.task
def scheduler_test() -> None:
    logger.info("This is a testing task.")
    print("Hello from test task!")


@app.task
def run_scheduled_task(scheduled_task_id: UUID=None) -> None:
    scheduled_task = ScheduledTask.objects.get(id=scheduled_task_id)

    _ = Task.objects.create(
                environment=scheduled_task.environment,
                creator=scheduled_task.creator,
                function=scheduled_task.function,
                parameters=scheduled_task.parameters,
                scheduled_task=scheduled_task,
            )


# def create_task(scheduled_task: ScheduledTask) -> UUID:
#     task = Task.objects.create(
#                 environment=scheduled_task.env,
#                 creator=request.user,
#                 function=scheduled_task.function,
#                 parameters=form.cleaned_data,
#             )
#     return task.id

# def create_celery_beat_schedule(scheduled_task) -> None:
#     get_or_create
