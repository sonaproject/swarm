import inspect

from xos.logger import Logger, logging, logger
from os.path import basename 

#logger = Logger(level=logging.INFO)
logger = Logger('/var/log/swarm_sync.log', loggername='DEBUG', level=logging.DEBUG)


def debug(msg):
    logger.debug(
                basename(str(inspect.stack()[1][1])) + ':' + 
                str(inspect.stack()[1][2]) + ' ' + 
                str(inspect.stack()[1][3]) + '()  ' + 
                str(msg))

def info(msg):
    logger.info(
                basename(str(inspect.stack()[1][1])) + ':' + 
                str(inspect.stack()[1][2]) + ' ' + 
                str(inspect.stack()[1][3]) + '()  ' + 
                str(msg))

def error(msg):
    logger.error(
                basename(str(inspect.stack()[1][1])) + ':' + 
                str(inspect.stack()[1][2]) + ' ' + 
                str(inspect.stack()[1][3]) + '()  ' + 
                str(msg))

