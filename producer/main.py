import os
import time
import random
import logging

from confluent_kafka import Producer


producer = Producer({'bootstrap.servers': os.environ['KAFKA_HOSTNAME']})
logger = logging.getLogger(__name__)


def on_success(err, msg):
    logger.info('got error %s', err)
    logger.info('got msg %s', msg)


while True:
    producer.poll(0)
    producer.produce('MyTopic', str(random.random()), callback=on_success)
    producer.flush()
    time.sleep(1)
