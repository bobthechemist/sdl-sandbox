import logging
import time

class myHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        attributes = dir(record)
        for a in attributes:
            try:
                value = getattr(record, a)
                print(f"{a}: {value}")
            except:
                print(f"{a} not found")

        log_entry = self.format(record)
        print(log_entry)
        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(record.created)))

log = logging.getLogger('test')
log.setLevel(logging.DEBUG)

custom_handler = myHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
custom_handler.setFormatter(formatter)

log.addHandler(custom_handler)

log.debug("This is a debug message")