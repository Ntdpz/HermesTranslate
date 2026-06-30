import os

from dotenv import load_dotenv

load_dotenv()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:***@localhost/")
QUEUE_NAME = os.getenv("QUEUE_NAME", "translation_tasks")
