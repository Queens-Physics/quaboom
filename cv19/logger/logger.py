import logging
import sys
from logging import handlers


class Logger(object):
    """
    Singleton Logger class. This class is only instantiated ONCE. It is to keep a consistent
    criteria for the logger throughout the application if need be called upon.
    It serves as the criteria for initiating logger for modules. It creates child loggers.
    It's important to note these are child loggers as any changes made to the root logger
    can be done.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls.debug_mode = True
            cls.formatter = logging.Formatter(
                "%(asctime)s — %(name)s — %(levelname)s — %(message)s"
            )
            cls.log_file = "log_file.log"

        return cls._instance

    def get_console_handler(self):
        """Defines a console handler to come out on the console
        Returns:
            logging handler object : the console handler
        """
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self.formatter)
        console_handler.name = "consoleHandler"
        return console_handler

    def get_file_handler(self):
        """Defines a file handler to come out on the console.
        Returns:
            logging handler object : the console handler
        """
        file_handler = handlers.RotatingFileHandler(
            self.log_file, maxBytes=5000, backupCount=1
        )
        file_handler.setFormatter(self.formatter)
        file_handler.name = "fileHandler"
        return file_handler

    def add_handlers(self, logger, handler_list: list):
        """Adds handlers to the logger, checks first if handlers exist to avoid
        duplication
        Args:
            logger: Logger to check handlers
            handler_list: list of handlers to add
        """
        existing_handler_names = []
        for existing_handler in logger.handlers:
            existing_handler_names.append(existing_handler.name)

        for new_handler in handler_list:
            if new_handler.name not in existing_handler_names:
                logger.addHandler(new_handler)

    def get_logger(self, logger_name: str):
        """Generates logger for use in the modules.
        Args:
            logger_name (string): name of the logger
        Returns:
            logger: returns logger for module
        """
        logger = logging.getLogger(logger_name)
        console_handler = self.get_console_handler()
        file_handler = self.get_file_handler()
        self.add_handlers(logger, [console_handler, file_handler])
        logger.propagate = False
        return logger

    def set_debug_mode(self, debug_mode: bool):
        """
        Function to set the root level logging to be debug level to be carried forward throughout
        Args:
            debug_mode (bool): debug mode initiation if true
        """
        if debug_mode:
            logging.root.setLevel(logging.DEBUG)
