import sys
import traceback
from judge_common import DB, Logger, Config
from judge_sender import send_tasks


def print_usage():
    print(f"usage: python {sys.argv[0]} <<pid>>")


def get_sid_list(pid: str):
    config = Config("./_config.yml")
    db = DB(config)

    template = "SELECT sid FROM submissions WHERE pid = %s"
    parameter_tuple = (pid,)
    result = db._query_all(template, parameter_tuple)

    return [row["sid"] for row in result]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print_usage()
        exit(1)

    pid = sys.argv[1]
    try:
        sid_list = get_sid_list(pid)
        send_tasks(sid_list)
    except Exception as e:
        Logger.error(traceback.format_exc())
