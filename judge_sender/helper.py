from typing import List
from judge_common import Config, CodePack, LazyLoadingCode, Logger
import traceback

from .style_check_handler import StyleCheckHandler
from .file_collector import FileCollectorFactory, FileCollector
from .context import Problem, Submission
from .db_agent import DBAgent
from .const import const


class InvalidSubmission(ValueError):
    pass


class InvalidLanguageId(ValueError):
    pass


def send_task(sid: str, file_collector: FileCollector, style_check_handler: StyleCheckHandler, language: int):
    code_pack = file_collector.build_code_pack()
    style_check_handler.handle(code_pack, language, const.AC)


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
                send_task(sid, file_collector, style_check_handler, problem.language)

            Logger.sid(sid, "done")
        except (InvalidSubmission, InvalidLanguageId) as e:
            Logger.warn(repr(e))
        except Exception as e:
            Logger.warn(traceback.format_exc())
