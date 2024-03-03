import asyncio
import logging
from asyncio import AbstractEventLoop
from concurrent.futures import Future
from time import time
from typing import Callable, Optional

from aiohttp import ClientSession


class StressTest:
    """Стресс тест."""

    def __init__(
        self,
        loop: AbstractEventLoop,
        url: str,
        total_requests: int,
        callback: Callable[[int, int], None],
        final_results: Callable[[dict], None],
    ) -> None:
        self._completed_reqiuests: int = 0
        self._load_test_future: Optional[Future] = None
        self._loop = loop
        self._url = url
        self._total_requests = total_requests
        self._callback = callback
        self._one_repsent = total_requests / 100
        self.responses = {}
        self.final_results = final_results

    def start(self):
        """Запуск сопрограммы запросов в отдельном цикле событий."""
        logging.info('Начало выполнения запросов')
        future = asyncio.run_coroutine_threadsafe(
            self._make_requests(), self._loop
        )
        self._load_test_future = future

    def cancel(self):
        """Остановка сопрограммы запросов."""
        logging.info('Остановка выполнения запросов')
        if self._load_test_future:
            self._loop.call_soon_threadsafe(self._load_test_future.cancel)

    async def write_results(self, result):
        """Распределение результатов запроса."""
        key = f'Response {result}'
        if self.responses.get(key):
            self.responses[key] += 1
        else:
            self.responses[key] = 1

    async def send_data_to_callback(self):
        """
        Отправка данных о ходе выполнения
         запросов в метод обновления данных очереди."""
        if (
            self._completed_reqiuests % self._one_repsent == 0
            or self._completed_reqiuests == self._total_requests
        ):
            logging.info(
                f'Запросов завершено: '
                f'{self._completed_reqiuests}/{self._total_requests}'
            )
            logging.info(
                f'Текущая статистика ответов от сервера: {self.responses}'
            )
            self._callback(self._completed_reqiuests, self._total_requests)

    async def _get_url(self, session: ClientSession, url: str):
        """Запрос к целевому адресу."""
        try:
            result = await session.get(url)
            result = result.status
        except Exception as error:
            result = error.__doc__
            logging.error(result)
        finally:
            self._completed_reqiuests += 1
            await self.write_results(result)
            await self.send_data_to_callback()

    async def _make_requests(self):
        """Создание пула запросов, инициализация их выполнения."""
        start = time()
        logging.info('Старт запросов к целевому адресу.')
        async with ClientSession() as session:
            reqs = (
                self._get_url(session, self._url)
                for _ in range(self._total_requests)
            )
            await asyncio.gather(*reqs)
            logging.info(
                f'Итоговая статистика ответов от сервера: {self.responses}'
            )
            self.work_time = time() - start
            self.final_results(self.responses, self.work_time)
