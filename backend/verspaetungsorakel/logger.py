import logging


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

formatter = logging.Formatter(
    "[%(asctime)s] [%(module)s/%(levelname)s]: %(message)s",
    datefmt="%d-%m-%y %H:%M:%S"
)

LEVEL = logging.DEBUG

console_handler = logging.StreamHandler()
console_handler.setLevel(LEVEL)
console_handler.setFormatter(formatter)
log.addHandler(console_handler)

file_handler = logging.FileHandler("latest.log")
file_handler.setLevel(LEVEL)
file_handler.setFormatter(formatter)
log.addHandler(file_handler)