import json
import os
import ssl

import pika

from .handlers import deploy_plugin, start_plugin, stop_plugin, task_plugin


def start_listening():
    host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    port = os.getenv("RABBITMQ_PORT", 5672)
    username = os.getenv("RABBITMQ_USER", "bugsbunny")
    password = os.getenv("RABBITMQ_PASSWORD", "wascallywabbit")

    connection = _build_connection(host, port, username, password)

    try:
        connection.ioloop.start()
    except KeyboardInterrupt:
        connection.close()

        # Loop until we're fully closed, will stop on its own
        connection.ioloop.start()


def _on_connected(connection):
    """Called when we are fully connected to RabbitMQ"""
    print("connected...")
    connection.channel(on_open_callback=_on_channel_open)


def _on_channel_open(new_channel):
    """Called when our channel has opened"""
    print("channel opened...")
    global channel
    channel = new_channel
    channel.queue_declare(
        queue="plugin_runner",
        durable=True,
        exclusive=False,
        auto_delete=False,
        callback=_on_queue_declared,
    )


def _on_queue_declared(frame):
    """Called when RabbitMQ has told us our Queue has been declared"""
    print("queue declared...")
    channel.basic_consume("plugin_runner", _handle_delivery)


def _handle_delivery(channel, deliver, properties, body):
    """Called when we receive a message from RabbitMQ"""
    print("received message!...")
    print(body.decode())

    try:
        msg_type = properties.headers.get("x-msg-type", "__NONE__")
        body_dict = json.loads(body.decode())

        match msg_type:
            case "DEPLOY_PLUGIN":
                deploy_plugin.delay(**body_dict)
            case "START_PLUGIN":
                start_plugin.delay(**body_dict)
            case "STOP_PLUGIN":
                stop_plugin.delay(**body_dict)
            case "TASK_PLUGIN":
                task_plugin.delay(body_dict)

        channel.basic_ack(deliver.delivery_tag)
    except Exception as exc:
        print(f"Error handling message: {exc}")


def _build_connection(host, port, username, password):
    # home = os.environ["HOME"]
    # context = ssl.create_default_context(
    #    cafile=f"{home}/dev/dev-utils/certs/ca-root.crt"
    # )
    # context.load_cert_chain(
    #    f"{home}/dev/dev-utils/beer-garden/certs/bgadmin.crt",
    #    f"{home}/dev/dev-utils/beer-garden/certs/bgadmin.key",
    # )
    # ssl_options = pika.SSLOptions(context, "localhost")
    ssl_options = None
    credentials = pika.PlainCredentials(username, password)
    parameters = pika.ConnectionParameters(
        host=host, port=port, credentials=credentials, ssl_options=ssl_options
    )

    return pika.SelectConnection(parameters, on_open_callback=_on_connected)
