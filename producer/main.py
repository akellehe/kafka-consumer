import os
import sys
import time
import random
import logging

from confluent_kafka import Producer

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

logger = logging.getLogger(os.environ['APP_NAME'])

while True:
    try:
        producer = Producer({'bootstrap.servers': os.environ['KAFKA_HOSTNAME']})
        break
    except:
        time.sleep(1)


def on_success(err, msg):
    logger.info('got error %s', err)
    logger.info('got msg %s', msg)


while True:
    producer.poll(0)
    producer.produce('MyTopic', str(random.random()), callback=on_success)
    producer.flush()
    time.sleep(1)
