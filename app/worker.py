import asyncio
import json

import aio_pika
from sqlalchemy import update

from app.config import QUEUE_NAME, RABBITMQ_URL
from app.db.database import async_session_factory
from app.db.models import TaskRecord
from app.agents.main_agent import build_context
from app.agents.translate_agent import translate
from app.agents.validate_agent import validate

MAX_RETRIES = 3


async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        body = json.loads(message.body.decode())
        task_id = body.get("task_id")
        text = body.get("text")
        if not task_id:
            return

        async with async_session_factory() as session:
            existing = await session.get(TaskRecord, task_id)
            if existing:
                return
            context_md = build_context(task_id, text)
            record = TaskRecord(
                task_id=task_id,
                status="translating",
                original_text=text,
                context_md=context_md,
            )
            session.add(record)
            await session.commit()

            for attempt in range(1, MAX_RETRIES + 2):
                translated = translate(context_md)
                valid = validate(translated)

                if valid:
                    record.retry_count = attempt - 1
                    record.status = "completed"
                    record.result_text = translated
                    break
                elif attempt <= MAX_RETRIES:
                    record.retry_count = attempt
                    record.status = "translating"
                else:
                    record.retry_count = MAX_RETRIES
                    record.status = "failed"
                    record.result_text = translated

                context_md = build_context(task_id, text) + (
                    f"\n\n## Retry #{attempt}\n"
                    f"Previous attempt still contained rule violations. "
                    f"Ensure ALL matched rules are applied.\n"
                )

            await session.commit()


async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        await queue.consume(process_message)
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
