from __future__ import annotations

import os
import time
import traceback
from typing import TYPE_CHECKING, Dict, NoReturn

import pymysql
from judge_common import DB, CodePack, Config, LazyLoadingCode, Logger

# user defined module
import const
from judge_sender.context import (
    Context,
    ContextFactory,
    Judger,
    Problem,
    Result,
    Submission,
)
from judge_sender.db_agent import DBAgent
from judge_sender.file_collector import FileCollectorFactory
from judge_sender.receiver_agent import ReceiverAgent
from judge_sender.style_check_handler import StyleCheckHandler

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


def get_language_extension(filename):
    return filename.split(".")[-1]


def judge_submission(
    context: Context,
    db_agent: DBAgent,
    style_check_handler,
    receiver_agent: ReceiverAgent,
    file_collector: FileCollector,
) -> NoReturn:
    sid = context.submission.sid
    pid = context.problem.pid
    language = context.problem.language
    config = context.config

    Logger.sid(sid, "RUN sid %d pid %d language %d" % (sid, pid, language))

    # Send submission codes from the user.
    for file_entity in file_collector.get_full_send_list():
        receiver_agent.send_file(file_entity[0], file_entity[1])

    # Build CodePack
    code_pack = CodePack(sid)
    if language == 0:
        file_entity = file_collector.get_submission_file_list()[0]
        code_pack.add_code(LazyLoadingCode("main", "c", file_entity[0]))
    else:
        for file_entity in file_collector.get_submission_file_list():
            code_pack.add_code(LazyLoadingCode(file_entity[1], get_language_extension(file_entity[1]), file_entity[0]))
    context.submission.code_pack = code_pack

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

    # Read the result.
    result = receiver_agent.read_result(context)
    context.result = result

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

    # Postprocess: Generate style check report.
    # Only generate report for ac submissions.
    if result.status_code == const.AC and language == 1:
        style_check_handler.handle(code_pack)

    # Update judge result to the database.
    db_agent.update_submission(sid, result)


def get_judger_user(sid, pid, language, butler_config):

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
        account, address = get_judger_user(sid, pid, language, butler_config)

        judger = Judger(address, account)
        receiver_agent = ReceiverAgent(judger)

        context = context_factory.create_context(problem, submission, judger)
        file_collector = file_collector_facotry.create_file_collector(problem, submission)

        judge_submission(context, db_agent, style_check_handler, receiver_agent, file_collector)

        Logger.info("Finish judging")


if __name__ == "__main__":
    while True:
        try:
            main()

        except pymysql.err.OperationalError as err:
            Logger.error(err)
            traceback.print_exc()

        except DB.DBLostConnection as err:
            Logger.error(err)
            traceback.print_exc()

        except Exception as err:
            Logger.error(err)
            raise err

        time.sleep(5)
