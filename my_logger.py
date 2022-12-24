import logging


def init_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # create file and stream handlers and set level to debug
    fh = logging.FileHandler(filename='files_load_api.log')
    sh = logging.StreamHandler()
    fh.setLevel(logging.DEBUG)
    sh.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s - %(funcName)s - %(message)s')
    # add formatter to fh and sh
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)
    # add fh and sh to logger
    logger.addHandler(fh)
    logger.addHandler(sh)
    logger.propagate = False
    return logger
