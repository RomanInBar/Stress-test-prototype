import asyncio

from gui_tkinter import StressTestGUI
from log import logger as logging
from thread_settings import ThreadsEventLoop


def main():
    logging.info('Инициализация цикла событий asyncio')
    loop = asyncio.new_event_loop()
    logging.info('Инициализация дочернего потока')
    asyncio_thread = ThreadsEventLoop(loop)
    logging.info('Запуск дочернего потока с asyncio в фоновом режиме')
    asyncio_thread.start()
    logging.info('Инитиализация объекта графического интерфейса')
    app = StressTestGUI(loop)
    logging.info(
        'Запуск бесконечного цикла в главном потоке(графический интерфейс)'
    )
    app.mainloop()


if __name__ == '__main__':
    main()
