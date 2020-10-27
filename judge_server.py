import binascii
import os
import subprocess
import sys
import time

# user defined module
import const, pika
from judge_common import Config, DB, Logger, WorkQueueSender, LazyLoadingCode, CodePackSerializer, CodePack

def send(ofp, lname, rname):
    assert os.system('cd /run/shm; ln -s \'%s\' \'%s\'; tar ch \'%s\' | gzip -1 > judge_server.tgz' % (os.path.realpath(lname), rname, rname)) == 0
    with open('/run/shm/judge_server.tgz', 'rb') as fp: b = fp.read()
    os.remove('/run/shm/%s' % rname)
    os.remove('/run/shm/judge_server.tgz')
    b = binascii.hexlify(b)
    ofp.write(('%10d' % len(b)).encode())
    ofp.write(b)
    ofp.flush()

def has_banned_word(lng, pid, sid, banned_words):
    submission_dir = '../submission'
    sourceList = '../testdata/{}/source.lst'.format(pid)
    check_script = 'scripts/banWordCheck.py'

    if lng != 0:
        file_num = 1
    else:
        file_num = 0
        with open(sourceList) as fp:
            for filename in fp.readlines():
                file_num += 1

    for file_count in range(file_num):
        filename = '../submission/{}-{}'.format(sid, file_count)

        for ban_word in banned_words:
            if os.system('{} {} {}'.format(check_script, filename, ban_word)) != 0:
                return True

    Logger.info('Passed ban words check')

    return False

# for non AC result, we can give messages that shows in the result of the submission to user
def leave_error_message(sid, message):
    filename = '../submission/{}-z'.format(sid)
    assert os.system('echo "{}" >> {}'.format(message, filename)) == 0

def get_language_extension(filename):
    return filename.split('.')[-1]

def judge_submission(sid, pid, lng, serv, db, config, handle_style_check):
    Logger.sid(sid, 'RUN sid %d pid %d lng %d' % (sid, pid, lng))

    p = subprocess.Popen(['ssh', serv, 'export PATH=$PATH:/home/butler; butler'], stdin = subprocess.PIPE, stdout = subprocess.PIPE)
    ifp = p.stdout
    ofp = p.stdin
    send(ofp, './const.py', 'const.py')
    send(ofp, '../testdata/%d/judge' % pid, 'judge')
    code_pack = CodePack(sid)

    # send submission codes from the user
    if lng != 0:
        source_name = 'main.c' # default name of source file. should change if we allow other language
        source_file = '../submission/{}-0'.format(sid)

        send(ofp, source_file, 'source')
        code_pack.add_code(LazyLoadingCode(source_name, 'c', source_file))
    else:
        with open('../testdata/%d/source.lst' % pid) as fp:
            i = 0
            for fn in fp.readlines():
                source_name = fn[:-1]
                source_file = '../submission/{}-{}'.format(sid, i)

                send(ofp, source_file, source_name)
                code_pack.add_code(LazyLoadingCode(source_name, get_language_extension(source_name), source_file))

                i += 1

    # send prepared codes from TA
    try:
        with open('../testdata/%d/send.lst' % pid) as fp:
            for fn in fp.readlines():
                send(ofp, '../testdata/%d/%s' % (pid, fn[:-1]), fn[:-1])
    except:
        pass
    ofp.write(('%10d' % -lng).encode())
    ofp.flush()
    while True:
        n = int(ifp.read(2))
        if n <= 0: break
        fn = ifp.read(n).decode()
        send(ofp, '../testdata/%d/%s' % (pid, fn), fn)
    score = int(ifp.readline())
    result = int(ifp.readline())
    cpu = int(ifp.readline())
    mem = int(ifp.readline())
    dtl = ifp.read()
    if dtl:
        with open('../submission/%d-z' % sid, 'wb') as fp: fp.write(dtl)

    Logger.sid(sid, 'GET sid %d time %d space %d score %d' % (sid, cpu, mem, score))

    if result == const.AC and cpu < config['BANNED_WORDS']['cpu_time_threshold'] and has_banned_word(lng, pid, sid, config['BANNED_WORDS']['word_list']):
        Logger.warn('found banned word, execute')

        db.update_submission(-1, 4, cpu, mem, sid)
        return

    # do style check if code passes
    if result == const.AC and lng == 1:
        handle_style_check(code_pack)

    db.update_submission(score, result, cpu, mem, sid)

def get_judger_user(sid, pid, lng, butler_config):

    # default judging host
    address = butler_config['host']
    account = butler_config['user']

    # check if the problem has specified a judging host
    try:
        with open('../testdata/%d/server.py' % pid) as fp:
            info = eval(fp.read())
            (address, account) = (info[0][0], info[0][1])
    except:
        pass

    return '{}@{}'.format(account, address)

def get_style_check_handler(config):
    # get work queue sender

    if config['STYLE_CHECK']['enabled']:
        work_queue_sender = WorkQueueSender(config['RBMQ']['host'], 'style_check_task')
        serializer = CodePackSerializer()

        def handler(code_pack):
            if len(code_pack) != 1:
                return

            code_pack_str = serializer.serialize(code_pack)
            work_queue_sender.send(code_pack_str)

            return
    else:
        def handler(code_pack):
            # do nothing
            return False

    return handler

def main():
    config = Config('_config.yml')

    # get butler config
    butler_config = config['BUTLER']

    # get database
    db = DB(config)

    # style check handler
    handle_style_check = get_style_check_handler(config)

    # start polling
    Logger.info('Load submitted code ...')
    while True:
        # get submission info
        row = db.get_next_submission_to_judge()

        if row == None:
            time.sleep(butler_config['period'])
            continue

        [sid, pid, lng] = row
        Logger.run("Start judging a submission")
        judger_user = get_judger_user(sid, pid, lng, butler_config)
        judge_submission(sid, pid, lng, judger_user, db, config, handle_style_check)

        Logger.info('Finish judging')

if __name__ == '__main__':
    while(True):
        try:
            main()

        except pika.exceptions.StreamLostError as e:
            Logger.error(e)

        except Exception as e:
            Logger.error(e)
            raise e

        time.sleep(5)
