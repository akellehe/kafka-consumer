import os
import logging

from confluent_kafka import Consumer


logger = logging.getLogger(__name__)
consumer = Consumer({'bootstrap.servers': os.environ['KAFKA_HOSTNAME'],
                     'group.id': os.environ['APP_NAME'],
                     'auto.offset.reset': 'earliest'})

consumer.subscribe(os.environ['TOPICS'].split(','))


while True:
    msg = consumer.poll(1.0)

    if msg is None:
        continue
    elif msg.error():
        logger.info('Got an error in the consumer %s', msg.error())
        continue

    logger.info("we got a message! %s", msg.value().decode('utf-8'))


c.close()

