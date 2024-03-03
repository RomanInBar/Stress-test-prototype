import logging

PATHC = 'Stress-test-prototype/stress-test.log'

logging.basicConfig(
    level=logging.INFO,
    filename=PATHC,
    filemode='w',
    format='''
    %(levelname)s [%(asctime)s] %(filename)s > %(funcName)s
     >>> %(message)s''',
    encoding='utf8',
)

logger = logging.getLogger()
