import sys
from colorama import Fore, Back, Style
from datetime import datetime

class Logger:
    F_RED = Fore.RED
    F_GREEN = Fore.GREEN
    F_BLUE = Fore.BLUE
    F_YELLOW = Fore.YELLOW
    F_CYAN = Fore.CYAN
    F_MAGENTA = Fore.MAGENTA
    S_DIM = Style.DIM
    S_RESET_ALL = Style.RESET_ALL

    TAG_LENGTH = 7

    @classmethod
    def info(cls, message):
        cls.color_stderr(cls.F_CYAN, 'INFO', message)

    @classmethod
    def warn(cls, message):
        cls.color_stderr(cls.F_YELLOW, 'WARN', message)

    @classmethod
    def run(cls, message):
        cls.color_stderr(cls.F_BLUE, 'RUN', message)

    @classmethod
    def sid(cls, sid, message):
        cls.color_stderr(cls.F_GREEN, sid, message)

    @classmethod
    def color_stderr(cls, color, tag, message):
        tag = '{tag:<{tag_length}}'.format(tag_length=cls.TAG_LENGTH, tag=tag)
        color_tag = '{}{}{}{}'.format(color, cls.S_DIM, tag, cls.S_RESET_ALL)
        color_time = '{}{}{}{}'.format(cls.F_YELLOW, cls.S_DIM, cls.get_time(), cls.S_RESET_ALL)
        prefix = '[{}]({}) '.format(color_tag, color_time)

        print('{} {}'.format(prefix, message))

    @classmethod
    def get_time(cls):
        return datetime.now().strftime('%H:%M:%S')
