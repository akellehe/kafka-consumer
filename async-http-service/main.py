import asyncio
import logging
import sys
import os

import tornado.ioloop
import tornado.web
import tornado.platform.asyncio


logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

logger = logging.getLogger(os.environ['APP_NAME'])


class MainHandler(tornado.web.RequestHandler):

    async def get(self):
        logger.info("Request received. Sleeping.")
        await asyncio.sleep(5)
        self.write("Hello, world")
        logger.info("Responding...")


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(int(os.environ['PORT']))
    tornado.platform.asyncio.AsyncIOMainLoop().start()
