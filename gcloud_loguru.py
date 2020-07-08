#!/usr/bin/env python
import sys
import traceback
import functools

import google.cloud.logging
from loguru import logger

def without_keys(d, keys):
    return {x: d[x] for x in d if x not in keys}

class StackDriverSink:
    def __init__(self, logger_name):
        self.logging_client = google.cloud.logging.Client()
        self.logger = self.logging_client.logger(logger_name)
        
    def write(self, message):
        '''
        source: https://github.com/Delgan/loguru/blob/master/loguru/_handler.py
        '''
        record = message.record
        log_info = {
            "elapsed": {
                "microseconds": record["elapsed"] // record["elapsed"].resolution,
                "seconds": record["elapsed"].total_seconds(),
            },
            "exception": (None if record["exception"] is None
                          else ''.join(traceback.format_exception(None, 
                                                                  record["exception"].value, 
                                                                  record["exception"].traceback))),
            "message": record["message"],
            "module": record["module"],
            "name": record["name"],
            "process": {"id": record["process"].id, "name": record["process"].name},
            "thread": {"id": record["thread"].id, "name": record["thread"].name},
            "extra": {k: str(v) 
                      for k, v in record["extra"].items()
                      if 'record' not in record["extra"]}
        }
        self.logger.log_struct(log_info, 
                               severity=record['level'].name,
                               source_location={'file': record['file'].name, 
                                                'function': record["function"], 
                                                'line': record["line"]})

def logger_wraps(*, entry=True, exit=True, level="DEBUG"):
    def wrapper(func):
        name = func.__name__

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            logger_ = logger.opt(depth=1)
            if entry:
                logger_.log(level, "Entering '{}' (args={}, kwargs={})", name, args, kwargs)
            result = func(*args, **kwargs)
            if exit:
                logger_.log(level, "Exiting '{}' (result={})", name, result)
            return result

        return wrapped

    return wrapper

def write_example(logger_name):
    """Writes log entries to the given logger."""
    logger.add(StackDriverSink(logger_name))
    logger.info('Hello, world!')
    logger.debug('Goodbye, world!')
    with logger.catch(message='devide by zero'): #, onerror=lambda _: sys.exit(1)):
        1/0
    print('Wrote logs to {}.'.format(logger))

if __name__ == '__main__':
    write_example('my-loguru')
