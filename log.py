import logging


logging.basicConfig(
    level=logging.INFO,
    filename='stress-test.log',
    filemode='w',
    format='''
    %(levelname)s [%(asctime)s] %(filename)s > %(funcName)s
     >>> %(message)s''',
    encoding='utf8',
)

logger = logging.getLogger()
