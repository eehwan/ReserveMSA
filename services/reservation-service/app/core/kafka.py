from shared.kafka.producer import KafkaProducer
from shared.config import settings

kafka_producer = KafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
