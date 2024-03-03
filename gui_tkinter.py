import logging
from queue import Queue
from time import time
from tkinter import Entry, Label, Tk, ttk

from loop_requests import StressTest


class StressTestGUI(Tk):
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
            f'Обновление очереди. Завершено {
                int(completed_requests / total_requests * 100)
            }%'
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
                    f'Пустая очередь, перезапуск '
                    f'_pool_queue через {self._refresh_ms}ms'
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
