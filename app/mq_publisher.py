import json

import aio_pika

from app.config import QUEUE_NAME, RABBITMQ_URL

_connection = None
_channel = None


async def _get_connection():
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(RABBITMQ_URL)
    return _connection


async def _get_channel():
    global _channel
    connection = await _get_connection()
    if _channel is None or _channel.is_closed:
        _channel = await connection.channel()
        await _channel.declare_queue(QUEUE_NAME, durable=True)
    return _channel


async def publish_task(task_id: str, text: str):
    channel = await _get_channel()
    message_body = json.dumps({"task_id": task_id, "text": text})
    await channel.default_exchange.publish(
        aio_pika.Message(body=message_body.encode()),
        routing_key=QUEUE_NAME,
    )


async def close_connection():
    global _connection, _channel
    if _channel and not _channel.is_closed:
        await _channel.close()
    if _connection and not _connection.is_closed:
        await _connection.close()
