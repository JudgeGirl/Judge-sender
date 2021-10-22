from typing import List
from judge_common import Config

from judge_sender.style_check_handler import StyleCheckHandler
from judge_sender.file_collector import FileCollectorFactory, FileCollector
from judge_sender.context import Problem, Submission
from judge_sender.db_agent import DBAgent


class InvalidSubmission(ValueError):
    pass


def send_task(sid: str, style_check_handler: StyleCheckHandler, file_collector_facotry: FileCollectorFactory):
    print(sid)


def send_tasks(sid_list: List[str]):
    config = Config("./_config.yml")
    db_agent = DBAgent(config)
    style_check_handler = StyleCheckHandler(config)
    file_collector_facotry = FileCollectorFactory(config["RESOURCE"]["testdata"], config["RESOURCE"]["submission"])

    for sid in sid_list:
        try:
            submission = db_agent.get_submission(sid)
            if submission is None:
                raise InvalidSubmission(f"sid: {sid}")
            else:
                print(f"submission: {submission}")
                problem = Problem(submission["pid"], submission["lng"])
                submission = Submission(sid)
                #  send_task(sid, style_check_handler, file_collector_facotry)
        except Exception as e:
            print(repr(e))
