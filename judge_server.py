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
from judge_sender.style_check_handler import StyleCheckHandler

resource: Dict[str, int] = {}


def send(output_pipe, source_name, result_name):
    """

    Args:
        source_name: The file or directory which we deliver to the receiver in hex string.
        result_name: The name which we rename the source file to.

    """
    assert (
        os.system(
            "cd /run/shm; ln -s '%s' '%s'; tar ch '%s' | gzip -1 > judge_server.tgz"
            % (os.path.realpath(source_name), result_name, result_name)
        )
        == 0
    )
    with open("/run/shm/judge_server.tgz", "rb") as opened_file:
        binary_data = opened_file.read()
    os.remove("/run/shm/%s" % result_name)
    os.remove("/run/shm/judge_server.tgz")
    hex_data = binascii.hexlify(binary_data)
    output_pipe.write(("%10d" % len(hex_data)).encode())
    output_pipe.write(hex_data)
    output_pipe.flush()


def has_banned_word(language, pid, sid, banned_words):
    submission_dir = "../submission"
    sourceList = f'{resource["testdata"]}/{pid}/source.lst'
    check_script = "scripts/banWordCheck.py"

    if language != 0:
        file_amount = 1
    else:
        file_amount = 0
        with open(sourceList) as opened_file:
            for filename in opened_file.readlines():
                file_amount += 1

    for file_count in range(file_amount):
        filename = "../submission/{}-{}".format(sid, file_count)

        for ban_word in banned_words:
            if os.system("{} {} {}".format(check_script, filename, ban_word)) != 0:
                return True

    Logger.info("Passed ban words check")

    return False


# for non AC result, we can give messages that shows in the result of the submission to user
def leave_error_message(sid, message):
    filename = "../submission/{}-z".format(sid)
    assert os.system('echo "{}" > {}'.format(message, filename)) == 0


def get_language_extension(filename):
    return filename.split(".")[-1]


def judge_submission(sid, pid, language, reciver, db, config, style_check_handler):
    Logger.sid(sid, "RUN sid %d pid %d language %d" % (sid, pid, language))

    popen_obj = subprocess.Popen(
        ["ssh", reciver, "export PATH=$PATH:/home/butler; butler"], stdin=subprocess.PIPE, stdout=subprocess.PIPE
    )
    input_file_pipe = popen_obj.stdout
    output_pipe = popen_obj.stdin

    # Send common judge scripts.
    send(output_pipe, "./const.py", "const.py")
    send(output_pipe, f'{resource["testdata"]}/{pid}/judge', "judge")

    # Send submission codes from the user.
    code_pack = CodePack(sid)
    if language != 0:
        source_name = "main"  # Default name of source file. It should change if we allow other language.
        source_file = "../submission/{}-0".format(sid)

        send(output_pipe, source_file, "source")
        code_pack.add_code(LazyLoadingCode(source_name, "c", source_file))
    else:
        with open(f'{resource["testdata"]}/{pid}/source.lst') as opened_file:
            i = 0
            for submission_file in opened_file.readlines():
                source_name = submission_file[:-1]
                source_file = "../submission/{}-{}".format(sid, i)

                send(output_pipe, source_file, source_name)
                code_pack.add_code(LazyLoadingCode(source_name, get_language_extension(source_name), source_file))

                i += 1

    # Send prepared codes from TA
    try:
        with open(f'{resource["testdata"]}/{pid}/send.lst') as opened_file:
            for context_file in opened_file.readlines():
                source_code = context_file[:-1]
                send(output_pipe, f'{resource["testdata"]}/{pid}/{source_code}', source_code)
    except:
        pass

    # Ends transport for prepared files.
    output_pipe.write(("%10d" % -language).encode())
    output_pipe.flush()

    # Waiting for requests of additional files.
    while True:
        n = int(input_file_pipe.read(2))
        # Receiver send the code for the end of additional files.
        if n <= 0:
            break

        additional_file = input_file_pipe.read(n).decode()
        send(output_pipe, f'{resource["testdata"]}/{pid}/{additional_file}', additional_file)

    # Read the result.
    score = int(input_file_pipe.readline())
    result = int(input_file_pipe.readline())
    cpu = int(input_file_pipe.readline())
    mem = int(input_file_pipe.readline())
    result_description = input_file_pipe.read()

    Logger.sid(sid, "GET sid %d time %d space %d score %d" % (sid, cpu, mem, score))

    # Write result description to file.
    if result_description:
        with open("../submission/%d-z" % sid, "wb") as opened_file:
            opened_file.write(result_description)

    # Postprocess: Check for banned words.
    if (
        result == const.AC
        and cpu < config["BANNED_WORDS"]["cpu_time_threshold"]
        and has_banned_word(language, pid, sid, config["BANNED_WORDS"]["word_list"])
    ):
        Logger.warn("found banned word, execute")

        db.update_submission(-1, 4, cpu, mem, sid)
        return

    # Postprocess: Generate style check report.
    # Only generate report for ac submissions.
    if result == const.AC and language == 1:
        style_check_handler.handle(code_pack)

    # Update judge result to the database.
    db.update_submission(score, result, cpu, mem, sid)


def get_judger_user(sid, pid, language, butler_config):

    # default judging host
    address = butler_config["host"]
    account = butler_config["user"]

    # check if the problem has specified a judging host
    try:
        with open(f'{resource["testdata"]}/{pid}/server.py') as opened_file:
            info = eval(opened_file.read())
            (address, account) = (info[0][0], info[0][1])
    except:
        pass

    return "{}@{}".format(account, address)


def main():
    config = Config("_config.yml")

    # setup global resource path
    resource["testdata"] = config["RESOURCE"]["testdata"]

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
        judger_user = get_judger_user(sid, pid, language, butler_config)

        judge_submission(sid, pid, language, judger_user, db, config, style_check_handler)

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
