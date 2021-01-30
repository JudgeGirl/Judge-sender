import binascii
import os
import subprocess
import sys
import time
import traceback
from typing import Dict

import pika
import pymysql
from judge_common import DB, CodePack, Config, LazyLoadingCode, Logger

# user defined module
import const
from judge_sender.context import Judger, Result
from judge_sender.receiver_agent import ReceiverAgent
from judge_sender.style_check_handler import StyleCheckHandler

resource: Dict[str, int] = {}


def has_banned_word(language, pid, sid, banned_words):
    sourceList = "{}/{}/source.lst".format(resource["testdata"], pid)
    check_script = "scripts/banWordCheck.py"

    if language != 0:
        file_amount = 1
    else:
        file_amount = 0
        with open(sourceList) as opened_file:
            for filename in opened_file.readlines():
                file_amount += 1

    for file_count in range(file_amount):
        filename = "{}/{}-{}".format(resource["submission"], sid, file_count)

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


def judge_submission(sid, pid, language, db, config, style_check_handler, receiver_agent):
    Logger.sid(sid, "RUN sid %d pid %d language %d" % (sid, pid, language))

    # Send common judge scripts.
    receiver_agent.send_common_prepare_files(pid)

    # Send submission codes from the user.
    code_pack = CodePack(sid)
    if language != 0:
        source_name = "main"  # Default name of source file. It should change if we allow other language.
        source_file = "{}/{}-0".format(resource["submission"], sid)

        receiver_agent.send_file(source_file, "source")
        code_pack.add_code(LazyLoadingCode(source_name, "c", source_file))
    else:
        with open("{}/{}/source.lst".format(resource["testdata"], pid)) as opened_file:
            i = 0
            for submission_file in opened_file.readlines():
                source_name = submission_file[:-1]
                source_file = "{}/{}-{}".format(resource["submission"], sid, i)

                receiver_agent.send_file(source_file, source_name)
                code_pack.add_code(LazyLoadingCode(source_name, get_language_extension(source_name), source_file))

                i += 1

    # Send prepared codes from TA
    try:
        with open("{}/{}/send.lst".format(resource["testdata"], pid)) as opened_file:
            for context_file in opened_file.readlines():
                source_code = context_file[:-1]
                receiver_agent.send_file("{}/{}/{}".format(resource["testdata"], pid, source_code), source_code)
    except:
        pass

    # Ends transport for prepared files.
    receiver_agent.end_prepare(language)

    # Waiting for requests of additional files.
    while True:
        # Receiver send the code for the end of additional files.
        additional_file = receiver_agent.get_next_additional_file()
        if additional_file is None:
            break

        receiver_agent.send_file("{}/{}/{}".format(resource["testdata"], pid, additional_file), additional_file)

    # Read the result.
    result = receiver_agent.read_result()

    Logger.sid(sid, "GET sid %d time %d space %d score %d" % (sid, result.cpu, result.mem, result.score))

    # Write result description to file.
    if result.description:
        with open("{}/{}-z".format(resource["submission"], sid), "wb") as opened_file:
            opened_file.write(result.description)

    # Postprocess: Check for banned words.
    if (
        result.status_code == const.AC
        and result.cpu < config["BANNED_WORDS"]["cpu_time_threshold"]
        and has_banned_word(language, pid, sid, config["BANNED_WORDS"]["word_list"])
    ):
        Logger.warn("found banned word, execute")

        db.update_submission(-1, 4, result.cpu, result.mem, sid)
        return

    # Postprocess: Generate style check report.
    # Only generate report for ac submissions.
    if result.status_code == const.AC and language == 1:
        style_check_handler.handle(code_pack)

    # Update judge result to the database.
    db.update_submission(result.score, result.status_code, result.cpu, result.mem, sid)


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

    # setup global resource path
    resource["testdata"] = config["RESOURCE"]["testdata"]
    resource["submission"] = config["RESOURCE"]["submission"]

    # get butler config
    butler_config = config["BUTLER"]

    # get database
    db = DB(config)

    # style check handler
    style_check_handler = StyleCheckHandler(config)

    # start polling
    Logger.info("Load submitted code ...")
    while True:
        # get submission info
        row = db.get_next_submission_to_judge()

        style_check_handler.send_heartbeat()

        if row == None:
            time.sleep(butler_config["period"])
            continue

        [sid, pid, language] = row
        Logger.run("Start judging a submission")
        account, address = get_judger_user(sid, pid, language, butler_config)
        judger = Judger(address, account)

        receiver_agent = ReceiverAgent(config, judger)
        judge_submission(sid, pid, language, db, config, style_check_handler, receiver_agent)

        Logger.info("Finish judging")


if __name__ == "__main__":
    while True:
        try:
            main()

        except pymysql.err.OperationalError as err:
            Logger.error(err)
            traceback.print_exc()

            time.sleep(5)

        except Exception as err:
            Logger.error(err)
            raise err

        time.sleep(5)
