from __future__ import annotations

import os
import time
import traceback
from typing import TYPE_CHECKING, Dict
import pymysql
from judge_common import Config, DBLostConnection, Logger

# user defined module
from judge_sender.context import (
    Context,
    ContextFactory,
    FailedExecutionResult,
    Judger,
    Problem,
    Result,
    Submission,
)
from judge_sender.db_agent import DBAgent
from judge_sender.error import SourceListNotFoundError
from judge_sender.file_collector import FileCollectorFactory
from judge_sender.receiver_agent import ReceiverAgent
from judge_sender.style_check_handler import StyleCheckHandler
from judge_sender import const


if TYPE_CHECKING:
    from judge_sender.context import Context
    from judge_sender.file_collector import FileCollector

resource: Dict[str, int] = {}


def has_banned_word(context: Context, banned_words):
    sourceList = "{}/{}/source.lst".format(resource["testdata"], context.problem.pid)
    check_script = "scripts/banWordCheck.py"

    if context.problem.language != 0:
        file_amount = 1
    else:
        file_amount = 0
        with open(sourceList) as opened_file:
            for filename in opened_file.readlines():
                file_amount += 1

    for file_count in range(file_amount):
        filename = "{}/{}-{}".format(resource["submission"], context.submission.sid, file_count)

        for ban_word in banned_words:
            if os.system("{} {} {}".format(check_script, filename, ban_word)) != 0:
                return True

    Logger.info("Passed ban words check")

    return False


# for non AC result, we can give messages that shows in the result of the submission to user
def leave_error_message(sid, message):
    filename = "{}/{}-z".format(resource["submission"], sid)
    assert os.system('echo "{}" > {}'.format(message, filename)) == 0


def judge_submission(
    context: Context,
    db_agent: DBAgent,
    style_check_handler,
    receiver_agent: ReceiverAgent,
    file_collector: FileCollector,
) -> None:
    sid = context.submission.sid
    pid = context.problem.pid
    language = context.problem.language
    config = context.config

    Logger.sid(sid, "RUN sid %d pid %d language %d" % (sid, pid, language))

    try:
        file_transfer(receiver_agent, file_collector, language)
        result = read_receiver_result(context, receiver_agent)
    except SourceListNotFoundError as e:
        Logger.error(repr(e))
        result = FailedExecutionResult()

    Logger.sid(sid, "GET sid %d time %d space %d score %d" % (sid, result.cpu, result.mem, result.score))

    # Write result description to file.
    if result.description:
        with open("{}/{}-z".format(resource["submission"], sid), "wb") as opened_file:
            opened_file.write(result.description)

    # Postprocess: Check for banned words.
    if (
        result.status_code == const.AC
        and result.cpu < config["BANNED_WORDS"]["cpu_time_threshold"]
        and has_banned_word(context, config["BANNED_WORDS"]["word_list"])
    ):
        Logger.warn("found banned word, execute")

        result.score = -1  # Tag it so it can be found from database later on.
        result.status_code = const.RE

    # Update judge result to the database.
    db_agent.update_submission(sid, result)

    # Postprocess: Generate style check report.
    if not isinstance(result, FailedExecutionResult):
        code_pack = file_collector.build_code_pack()
        style_check_handler.handle(code_pack, language, result.status_code)
        context.submission.code_pack = code_pack


def read_receiver_result(context: Context, receiver_agent: ReceiverAgent) -> Result:
    result = receiver_agent.read_result(context)
    context.result = result

    return result


def file_transfer(receiver_agent: ReceiverAgent, file_collector: FileCollector, language):
    # Send submission codes from the user.
    for file_entity in file_collector.get_full_send_list():
        receiver_agent.send_file(file_entity[0], file_entity[1])

    # Ends transport for prepared files.
    receiver_agent.end_prepare(language)

    # Waiting for requests of additional files.
    while True:
        # Receiver send the code for the end of additional files.
        file_name = receiver_agent.get_next_additional_file()
        if file_name is None:
            break

        file_path = file_collector.get_additional_file_path(file_name)
        receiver_agent.send_file(file_path, file_name)


def get_judger_user(pid, butler_config):

    # default judging host
    address = butler_config["host"]
    account = butler_config["user"]

    # check if the problem has specified a judging host
    try:
        with open("{}/{}/server.py".format(resource["testdata"], pid)) as opened_file:
            info = eval(opened_file.read())
            (address, account) = (info[0][0], info[0][1])
    except:
        pass

    return account, address


def main():
    config = Config("_config.yml")
    context_factory = ContextFactory()
    file_collector_facotry = FileCollectorFactory(config["RESOURCE"]["testdata"], config["RESOURCE"]["submission"])

    # setup global resource path
    resource["testdata"] = config["RESOURCE"]["testdata"]
    resource["submission"] = config["RESOURCE"]["submission"]

    # get butler config
    butler_config = config["BUTLER"]

    # get database
    db_agent = DBAgent(config)

    # style check handler
    style_check_handler = StyleCheckHandler(config)

    # start polling
    Logger.info("Load submitted code ...")
    while True:
        style_check_handler.send_heartbeat()

        if db_agent.has_next_submission() == False:
            time.sleep(butler_config["period"])
            continue

        sid, pid, language = db_agent.get_next_submission()

        problem = Problem(pid, language)
        submission = Submission(sid)

        Logger.run("Start judging a submission")
        account, address = get_judger_user(pid, butler_config)

        judger = Judger(address, account)
        receiver_agent = ReceiverAgent(judger)

        context = context_factory.create_context(problem, submission, judger)
        file_collector = file_collector_facotry.create_file_collector(problem, submission)

        judge_submission(context, db_agent, style_check_handler, receiver_agent, file_collector)

        Logger.info("Finish judging")


if __name__ == "__main__":
    Logger.set_log_file("logs/log")
    while True:
        try:
            main()

        except pymysql.err.OperationalError as err:
            Logger.error(repr(err))
            traceback.print_exc()

        except DBLostConnection as err:
            Logger.error(repr(err))
            traceback.print_exc()

        except Exception as err:
            Logger.error(repr(err))
            raise err

        time.sleep(5)
