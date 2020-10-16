import binascii
import os
import signal
import pymysql
import MySQLdb
import subprocess
import sys
import time
import yaml
from colorama import Fore, Back, Style

def color_console(color, tag, message, out):
        print('[{}{}{}] {}'.format(color, tag, Fore.RESET, message), file=out)

def get_config(config_file):
        with open(config_file, 'r') as f:
                config = yaml.load(f.read())

        return config

def get_db(host, user, password, db_name):
        db = MySQLdb.connect(host=host, user=user, passwd=password, db=db_name)

        return db

def send(ofp, lname, rname):
        assert os.system('cd /run/shm; ln -s \'%s\' \'%s\'; tar ch \'%s\' | gzip -1 > judge_server.tgz' % (os.path.realpath(lname), rname, rname)) == 0
        with open('/run/shm/judge_server.tgz', 'rb') as fp: b = fp.read()
        os.remove('/run/shm/%s' % rname)
        os.remove('/run/shm/judge_server.tgz')
        b = binascii.hexlify(b)
        ofp.write(('%10d' % len(b)).encode())
        ofp.write(b)
        ofp.flush()

def has_banned_word(lng, pid, sid):
        submission_dir = '../submission'
        sourceList = '../testdata/{}/source.lst'.format(pid)
        check_script = 'scripts/banWordCheck.py'
        #  ban_word = 'fork'
        ban_word_list = ['fork', 'unistd', 'syscall']

        if lng != 0:
                file_num = 1
        else:
                file_num = 0
                with open(sourceList) as fp:
                        for filename in fp.readlines():
                                file_num += 1

        for file_count in range(file_num):
                filename = '../submission/{}-{}'.format(sid, file_count)

                for ban_word in ban_word_list:
                        if os.system('{} {} {}'.format(check_script, filename, ban_word)) != 0:
                                return True

        color_console(Fore.CYAN, 'INFO', 'passed ban word check', sys.stderr)
        return False

def updateSubmission(scr, res, cpu, mem, sid, cursor):
        query = 'UPDATE submissions SET scr = {}, res = {}, cpu={}, mem={} WHERE sid={}'.format(
                scr,
                res,
                cpu,
                mem,
                sid
        )
        cursor.execute(query)

def leaveErrorMessage(sid, message):
        filename = '../submission/{}-z'.format(sid)
        assert os.system('echo "{}" > {}'.format(message, filename)) == 0

def work(sid, pid, lng, serv, cursor):
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

        trigger_of_search_bad_word = 50
        result_AC = 7
        if result == result_AC and cpu < trigger_of_search_bad_word and has_banned_word(lng, pid, sid):
                color_console(FORE.red, 'WARN', 'found banned word, execute', sys.stderr)
                updateSubmission(-1, 4, cpu, mem, sid, cursor)
                return

        updateSubmission(score, result, cpu, mem, sid, cursor)

def prepare(sid, pid, lng, butler_config):

        address = butler_config['host']
        account = butler_config['user']
        try:
                with open('../testdata/%d/server.py' % pid) as fp:
                        info = eval(fp.read())
                        (address, account) = (info[0][0], info[0][1])
        except:
                pass

        return '{}@{}'.format(account, address)

def main():
        config = get_config('_config.yml')

        # get butler config
        butler_config = config['BUTLER']

        # get db cursor
        db_config = config['DATABASE']
        db = get_db(db_config['host'], db_config['user'], db_config['password'], db_config['database'])
        cursor = db.cursor()

        # start polling
        color_console(Fore.GREEN, 'INFO', 'Load submitted code ...', sys.stderr)
        while True:
                # get submission info
                cursor.execute('SELECT sid, pid, lng FROM submissions WHERE res = 0 ORDER BY sid LIMIT 1')
                row = cursor.fetchone()

                if row:
                        [sid, pid, lng] = map(int, row)
                        remote = prepare(sid, pid, lng, butler_config)
                        work(sid, pid, lng, remote, cursor)
                else:
                        time.sleep(butler_config['period'])

assert __name__ == '__main__'
main()
