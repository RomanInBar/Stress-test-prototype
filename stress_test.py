import asyncio
import logging
from asyncio import AbstractEventLoop
from concurrent.futures import Future
from queue import Queue
from threading import Thread
from time import time
from tkinter import Entry, Label, Tk, ttk
from typing import Callable, Optional

from aiohttp import ClientSession


logging.basicConfig(
    level=logging.INFO,
    filename='tkinter.log',
    filemode='w',
    format='%(funcName)s -- %(asctime)s: %(levelname)s %(message)s',
    encoding='utf8',
)


class LoadTester(Tk):
    """Графический интерфейс."""

    def __init__(self, loop, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        self._queue = Queue()
        self._refresh_ms = 25
        self._loop = loop
        self._load_test = None
        self.title('URL Requester')

        self._url_label = Label(self, text='URL')
        self._url_label.grid(column=0, row=0)

        self._url_field = Entry(self, width=30)
        self._url_field.grid(column=1, row=0, columnspan=3)

        self._request_label = Label(self, text='Number of requests:')
        self._request_label.grid(column=0, row=1)

        self._request_field = Entry(self, width=10)
        self._request_field.grid(column=1, row=1)

        self._submit = ttk.Button(self, text='Submit', command=self._start)
        self._submit.grid(column=2, row=1)

        self._pb_lable = Label(self, text='Progress')
        self._pb_lable.grid(column=0, row=3)

        self._pb = ttk.Progressbar(
            self, orient='horizontal', length=200, mode='determinate'
        )
        self._pb.grid(column=1, row=3, columnspan=2)

    def _update_bar(self, percent_complete: int):
        """Обновляет данные прогресс бара."""
        if percent_complete == 100:
            logging.info(f'Процесс выполнен на {percent_complete}%')
            self._load_test = None
            self._submit['text'] = 'Submit'
        else:
            logging.info('Отрисовка прогресса')
            self._pb['value'] = percent_complete
            self.after(self._refresh_ms, self._pool_queue)

    def _queue_update(self, completed_requests: int, total_requests: int):
        """Обновляет данные очереди."""
        logging.info(
            f'Обновление очереди. Завершено {int(completed_requests / total_requests * 100)}%'
        )
        self._queue.put(int(completed_requests / total_requests * 100))

    def _pool_queue(self):
        """Проверяет очередь на наличие значений."""
        if not self._queue.empty():
            logging.info('Получение последнего значения из очереди')
            percent_complete = self._queue.get()
            self._update_bar(percent_complete)
        else:
            if self._load_test:
                logging.info(
                    f'Пустая очередь, перезапуск _pool_queue через {self._refresh_ms}ms'
                )
                self.after(self._refresh_ms, self._pool_queue)

    def _start(self):
        """Запуск/остановка стресс теста"""
        if self._load_test is None:
            self._submit['text'] = 'Cancel'
            logging.info('Инициализация объекта StressTest')
            test = StressTest(
                self._loop,
                self._url_field.get(),
                int(self._request_field.get()),
                self._queue_update,
                self.show_final_results,
            )
            logging.info('Отложенный запуск _pool_queue')
            self.after(self._refresh_ms, self._pool_queue)
            logging.info('Старт стресс тестирования')
            test.start()
            self._load_test = test
        else:
            logging.info('Инициализвация остановки запросов к целевому сайту')
            self._load_test.cancel()
            self._load_test = None
            self._submit['text'] = 'Submit'

    def show_final_results(self, results: dict, work_time: time):
        """Вывод финальных результатов теста."""
        Label(self, text='Results:').grid(column=4, row=0)
        counter = 1
        for index, item in enumerate(results.items(), 1):
            response, total = item
            Label(self, text=f'{response}: {total}').grid(column=4, row=index)
            counter += index
        Label(self, text=f'Время работы: {work_time:.2f}c.').grid(
            column=4, row=counter
        )


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
        """Отправка данных о ходе выполнения запросов в метод обновления данных очереди."""
        if (
            self._completed_reqiuests % self._one_repsent == 0
            or self._completed_reqiuests == self._total_requests
        ):
            logging.info(
                f'Запросов завершено: {self._completed_reqiuests}/{self._total_requests}'
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
            reqs = [
                self._get_url(session, self._url)
                for _ in range(self._total_requests)
            ]
            await asyncio.gather(*reqs)
            logging.info(
                f'Итоговая статистика ответов от сервера:\n{self.responses}'
            )
            self.work_time = time() - start
            self.final_results(self.responses, self.work_time)


class ThreadsEventLoop(Thread):
    """Инициализация нового потока с циклом событий."""

    def __init__(self, loop: AbstractEventLoop):
        super().__init__()
        self._loop = loop
        self.daemon = True

    def run(self):
        logging.info('Запуск бесконечного цикла в дочернем потоке')
        self._loop.run_forever()


logging.info('Инициализация цикла событий asyncio')
loop = asyncio.new_event_loop()
logging.info('Инициализация дочернего потока')
asyncio_thread = ThreadsEventLoop(loop)
logging.info('Запуск дочернего потока с asyncio в фоновом режиме')
asyncio_thread.start()
logging.info('Инитиализация объекта графического интерфейса')
app = LoadTester(loop)
logging.info(
    'Запуск бесконечного цикла в главном потоке(графический интерфейс)'
)
app.mainloop()
