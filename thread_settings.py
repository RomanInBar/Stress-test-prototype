import logging
from asyncio.events import AbstractEventLoop
from threading import Thread


class ThreadsEventLoop(Thread):
    """Инициализация нового потока с циклом событий."""

    def __init__(self, loop: AbstractEventLoop):
        super().__init__()
        self._loop = loop
        self.daemon = True

    def run(self):
        logging.info('Запуск бесконечного цикла в потоке')
        self._loop.run_forever()
