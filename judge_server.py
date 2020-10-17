import binascii
import os
import subprocess
import sys
import time
import yaml
from colorama import Fore, Back, Style

# user defined module
import const
from common import Config, DB

def color_console(color, tag, message, out):
    print('[{}{:<4}{}] {}'.format(color, tag, Fore.RESET, message), file=out)

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

    color_console(Fore.YELLOW, 'INFO', 'passed ban words check', sys.stderr)

    return False

# for non AC result, we can give messages that shows in the result of the submission to user
def leave_error_message(sid, message):
    filename = '../submission/{}-z'.format(sid)
    assert os.system('echo "{}" >> {}'.format(message, filename)) == 0

def judge_submission(sid, pid, lng, serv, db, config):
    color_console(Fore.GREEN, 'RUN', 'sid %d pid %d lng %d' % (sid, pid, lng), sys.stderr)

    p = subprocess.Popen(['ssh', serv, 'export PATH=$PATH:/home/butler; butler'], stdin = subprocess.PIPE, stdout = subprocess.PIPE)
    ifp = p.stdout
    ofp = p.stdin
    send(ofp, './const.py', 'const.py')
    send(ofp, '../testdata/%d/judge' % pid, 'judge')
    if lng != 0:
        send(ofp, '../submission/%d-0' % sid, 'source')
    else:
        with open('../testdata/%d/source.lst' % pid) as fp:
            i = 0
            for fn in fp.readlines():
                send(ofp, '../submission/%d-%d' % (sid, i), fn[:-1])
                i += 1
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

    color_console(Fore.MAGENTA, 'GET', 'sid %d time %d space %d score %d' % (sid, cpu, mem, score), sys.stderr)

    if result == const.AC and cpu < config['BANNED_WORDS']['cpu_time_threshold'] and has_banned_word(lng, pid, sid, config['BANNED_WORDS']['word_list']):
        color_console(FORE.red, 'WARN', 'found banned word, execute', sys.stderr)

        db.update_submission(-1, 4, cpu, mem, sid)
        return

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

def main():
    config = Config('_config.yml')

    # get butler config
    butler_config = config['BUTLER']

    # get database
    db = DB(config)

    # start polling
    color_console(Fore.YELLOW, 'INFO', 'Load submitted code ...', sys.stderr)
    while True:
        # get submission info
        row = db.get_next_submission_to_judge()

        if row == None:
            time.sleep(butler_config['period'])
            continue

        [sid, pid, lng] = row
        judger_user = get_judger_user(sid, pid, lng, butler_config)
        judge_submission(sid, pid, lng, judger_user, db, config)

assert __name__ == '__main__'
main()
