from typing import List
from judge_common import Config, CodePack, LazyLoadingCode, Logger
import traceback

from judge_sender.style_check_handler import StyleCheckHandler
from judge_sender.file_collector import FileCollectorFactory, FileCollector
from judge_sender.context import Problem, Submission
from judge_sender.db_agent import DBAgent


class InvalidSubmission(ValueError):
    pass


class InvalidLanguageId(ValueError):
    pass


def send_task(sid: str, file_collector: FileCollector, style_check_handler: StyleCheckHandler):
    code_pack = CodePack(sid)
    if file_collector.problem.language != 1:
        raise InvalidLanguageId()

    file_entity = file_collector.get_submission_file_list()[0]
    code_pack.add_code(LazyLoadingCode("main", "c", file_entity[0]))
    style_check_handler.handle(code_pack)


def send_tasks(sid_list: List[str]):
    config = Config("./_config.yml")
    db_agent = DBAgent(config)
    style_check_handler = StyleCheckHandler(config)
    file_collector_facotry = FileCollectorFactory(config["RESOURCE"]["testdata"], config["RESOURCE"]["submission"])

    for sid in sid_list:
        Logger.sid(sid, "start")
        try:
            submission = db_agent.get_submission(sid)
            if submission is None:
                raise InvalidSubmission(f"sid: {sid}")
            else:
                problem = Problem(submission["pid"], submission["lng"])
                submission = Submission(sid)
                file_collector = file_collector_facotry.create_file_collector(problem, submission)
                send_task(sid, file_collector, style_check_handler)

            Logger.sid(sid, "done")
        except (InvalidSubmission, InvalidLanguageId) as e:
            Logger.warn(repr(e))
        except Exception as e:
            Logger.warn(traceback.format_exc())
