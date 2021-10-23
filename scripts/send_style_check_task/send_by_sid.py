import sys
import traceback
from judge_common import DB, Logger, Config

from helper import send_tasks


def print_usage():
    print(f"usage: python {sys.argv[0]} <<sid>>")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print_usage()
        exit(1)

    sid = sys.argv[1]
    try:
        send_tasks([sid])
    except Exception as e:
        Logger.error(traceback.format_exc())
