import os
import sys
import random
import time
import asyncio
import logging
import signal
import functools

import tornado.simple_httpclient
import tornado.httputil
import tornado.gen
from confluent_kafka import Consumer


HTTP_HOSTNAME = os.environ['HTTP_HOSTNAME']
HTTP_PORT = int(os.environ['HTTP_PORT'])
BATCH_SIZE = 10


logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

logger = logging.getLogger(os.environ['APP_NAME'])


def attempt_connection():
    """
    Attempts to initialize a connection to Kafka _once_. If we fail we just let that exception
    bubble to the calling context.

    :returns: confluent_kafka.Consumer
    """
    logging.info("Attempting to connect to Kafka...")
    consumer = Consumer({'bootstrap.servers': os.environ['KAFKA_HOSTNAME'],
                 'group.id': os.environ['APP_NAME'],
                 'auto.offset.reset': 'earliest'})
    consumer.subscribe(os.environ['TOPICS'].split(','))
    return consumer


def get_consumer():
    """
    There's no guarantee Kafka will be ready to accept connections when this runs. We don't want
    our consumer to just hang, so we retry until Kafka _is_ ready.

    :returns: confluent_kafka.Consumer
    """
    consumer = None
    while not consumer:
        consumer = attempt_connection()
        time.sleep(1)
    return consumer


def handle_disconnect(consumer, loop, signum, frame):
    """
    When process managers go to stop our task they usually issue SIGTERM. By catching and handling
    the signal we can ensure we clean up all the necessary resources so we don't have to forcibly
    kill the ioloop (which can leave open sockets and hanging connections).

    :param confluent_kafka.Consumer consumer: The consumer that's being run.
    :param asyncio.AsyncIOLoop loop: The currently running ioloop.
    :param signum: signal.SIGTERM
    :param frame: The python Frame running at the time the signal was thrown.
    """
    logging.info("Cleaning up.")
    consumer.close()
    loop.stop()


async def handle_message(http_client, consumer, msg):
    """
    Decode the message body (we expect utf-8) and log it. Then send that message to the
    async-http-service that is standing by. The really cool thing about this is that we can
    call `handle_message` a bunch of times and

    :param tornado.httpclient.AsyncHTTPClient http_client: A non-blocking HTTP client.
    :param confluent_kafka.Consumer consumer: The Kafka consumer that's running.
    :param msg: confluent_kafka.Message
    """
    value = msg.value().decode('utf-8')
    logger.info("handling message! %s", value)

    response = await http_client.fetch(
        tornado.httputil.url_concat(
            "{}:{}".format(HTTP_HOSTNAME, HTTP_PORT),
            {'number': str(random.random())}
        ),
        request_timeout=10, # Requests should be FAST
        raise_error=False
    )

    if 200 <= response.code < 300:
        logger.info("Got a successful response. committing.")
        consumer.commit(msg)
    else:
        logger.error('not committing.')


async def main(consumer, http_client):
    """
    Just keep listening for, and handling messages.

    :param confluent_kafka.Consumer consumer: The consumer listening for messages.
    :param tornado.httpclient.AsyncHTTPClient http_client: A non-blocking HTTP client.
    """
    while True:
        try:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            elif msg.error():
                logger.info('Got an error in the consumer %s', msg.error())
                await asyncio.sleep(1)
            await handle_message(http_client, consumer, msg)
        except asyncio.CancelledError:
            logger.info("Cancelling.")
            break


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    _consumer = get_consumer()
    _http_client = tornado.httpclient.AsyncHTTPClient(max_clients=BATCH_SIZE)

    signal.signal(signal.SIGTERM, functools.partial(handle_disconnect, _consumer, loop))

    tasks = [loop.create_task(main(_consumer, _http_client)) for i in range(BATCH_SIZE)]

    loop.run_forever()
