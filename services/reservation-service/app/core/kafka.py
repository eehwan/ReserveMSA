# Core kafka infrastructure only
from shared.kafka.producer import KafkaProducer
from shared.kafka.consumer import BaseKafkaConsumerManager
from shared.config import settings

# Producer instance management
kafka_producer_instance = None

async def get_kafka_producer_instance():
    global kafka_producer_instance
    if kafka_producer_instance is None:
        kafka_producer_instance = KafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
        await kafka_producer_instance.start()
    return kafka_producer_instance

async def start_kafka_producer():
    await get_kafka_producer_instance()

async def close_kafka_producer_instance():
    global kafka_producer_instance
    if kafka_producer_instance:
        await kafka_producer_instance.stop()
        kafka_producer_instance = None

# Consumer instance management
consumer_manager: BaseKafkaConsumerManager = None

async def initialize_consumer_manager(topic_handlers: dict):
    global consumer_manager
    if consumer_manager is not None:
        return

    consumer_manager = BaseKafkaConsumerManager(
        topic_handlers=topic_handlers,
        group_id="reservation-service-group",
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    )

async def start_kafka_consumers():
    if consumer_manager:
        await consumer_manager.start()

async def stop_kafka_consumers():
    if consumer_manager:
        await consumer_manager.stop()