# TODO: Create a proper pythonic structure and make this the __init__.py file

import logging
import os
import sys

running_in_docker: bool = False
launch_path = os.path.abspath(os.path.dirname(sys.argv[0]))
html_path = os.path.join(launch_path, "html")
port_http = 80
port_bona = 20008


def init_log(log_level: int = logging.INFO):
    log_path = os.path.join(launch_path, "status.log")

    if running_in_docker:
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(log_path)
    logging.Formatter('%(levelname)s: %(asctime)s\n%(message)s')
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(log_level)

    logging.info("Logger started")


if len(sys.argv) > 2:
    port_http = int(sys.argv[1])
    port_bona = int(sys.argv[2])

if len(sys.argv) > 3:
    running_in_docker = bool(sys.argv[3])

init_log()
