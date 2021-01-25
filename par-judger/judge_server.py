import binascii
import os
import queue
import signal
import subprocess
import sys
import threading
import time

import MySQLdb
import pymysql
import yaml
from colorama import Back, Fore, Style

WORKSPACE = "/home/judgesister/Judge-sender/par-judger/.."


def send(ofp, wid, lname, rname):
    working_dir = "/run/shm/judger%d" % (wid)
    assert os.system("mkdir -p %s" % (working_dir)) == 0
    assert (
        os.system(
            "cd %s; ln -s '%s' '%s'; tar ch '%s' | gzip -1 > judge_server.tgz"
            % (working_dir, os.path.realpath(lname), rname, rname)
        )
        == 0
    )
    with open("/%s/judge_server.tgz" % (working_dir), "rb") as fp:
        b = fp.read()
    os.remove("/%s/%s" % (working_dir, rname))
    os.remove("/%s/judge_server.tgz" % (working_dir))
    b = binascii.hexlify(b)
    ofp.write(("%10d" % len(b)).encode())
    ofp.write(b)
    ofp.flush()


def work(sid, pid, lng, wid, address, account):
    print("[" + Fore.GREEN + "Run" + Fore.RESET + "] sid %d pid %d lng %d" % (sid, pid, lng), file=sys.stderr)
    # construct ssh connection
    serv = "%s@%s" % (account, address)
    senv = "export PATH=$PATH:/home/%s" % (account)
    p = subprocess.Popen(["ssh", serv, "%s; butler" % senv], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    ifp = p.stdout
    ofp = p.stdin

    # send the data to remote server
    send(ofp, wid, "%s/./const.py" % WORKSPACE, "const.py")
    send(ofp, wid, "%s/../testdata/%d/judge" % (WORKSPACE, pid), "judge")
    if lng != 0:
        send(ofp, wid, "%s/../submission/%d-0" % (WORKSPACE, sid), "source")
    else:
        with open("%s/../testdata/%d/source.lst" % (WORKSPACE, pid)) as fp:
            i = 0
            for fn in fp.readlines():
                send(ofp, wid, "%s/../submission/%d-%d" % (WORKSPACE, sid, i), fn[:-1])
                i += 1
    try:
        with open("%s/../testdata/%d/send.lst" % (WORKSPACE, pid)) as fp:
            for fn in fp.readlines():
                send(ofp, wid, "%s/../testdata/%d/%s" % (WORKSPACE, pid, fn[:-1]), fn[:-1])
    except:
        pass
    ofp.write(("%10d" % -lng).encode())
    ofp.flush()
    while True:
        n = int(ifp.read(2))
        if n <= 0:
            break
        fn = ifp.read(n).decode()
        send(ofp, wid, "%s/../testdata/%d/%s" % (WORKSPACE, pid, fn), fn)
    score = int(ifp.readline())
    result = int(ifp.readline())
    cpu = int(ifp.readline())
    mem = int(ifp.readline())
    dtl = ifp.read()
    if dtl:
        with open("%s/../submission/%d-z" % (WORKSPACE, sid), "wb") as fp:
            fp.write(dtl)

    print(
        "[" + Fore.MAGENTA + "Get" + Fore.RESET + "] sid %d time %d space %d score %d" % (sid, cpu, mem, score),
        file=sys.stderr,
    )

    worker_cursor[wid].execute(
        "UPDATE submissions SET scr=%s, res=%s, cpu=%s, mem=%s WHERE sid=%s" % (score, result, cpu, mem, sid)
    )
    # db.commit()


def worker_judge(wid, butler_config, wlock, wlive, wset, wque):
    address = butler_config["host"]
    account = butler_config["user"]
    while True:
        if wque.empty():
            time.sleep(1)
            continue
        wlive[wid] = False
        sub = wque.get()
        print("Workder%d %s %s %s" % (wid, address, account, sub))
        work(sub[0], sub[1], sub[2], wid, address, account)
        wlock.acquire()
        wset.remove(int(sub[0]))
        wlock.release()
        time.sleep(1)
        wlive[wid] = True


def main(butler_config):
    print("[" + Fore.GREEN + "INFO" + Fore.RESET + "] Load submitted code ...", file=sys.stderr)
    """
	Create the worker
	"""
    workers = []
    wqueues = []
    wlive = []
    wlock = threading.Lock()
    wset = set()
    wsize = len(butler_config)

    for i in range(0, wsize):
        wque = queue.Queue()
        worker = threading.Thread(target=worker_judge, args=[i, butler_config[i], wlock, wlive, wset, wque])
        worker.start()
        workers.append(worker)
        wqueues.append(wque)
        wlive.append(True)

    """
	Push server
	"""
    while True:
        cursor.execute("SELECT sid, pid, lng FROM submissions WHERE res = 0 ORDER BY sid LIMIT 5")
        rows = cursor.fetchall()
        for sub in rows:
            # check in progress
            if int(sub[0]) in wset:
                continue

            hasAssigned = False
            (address, account) = ("localhost", "butler")
            try:
                with open("%s/../testdata/%d/server.py" % (WORKSPACE, sub[1])) as fp:
                    info = eval(fp.read())
                    hasAssigned = True
                    (address, account) = (info[0][0], info[0][1])
            except:
                pass

            # find the suitable worker
            for i in range(0, wsize):
                runnable = False
                if wlive[i] == False:
                    continue
                if wqueues[i].empty():
                    if hasAssigned:
                        if address == butler_config[i]["host"] and account == butler_config[i]["user"]:
                            runnable = True
                    else:
                        runnable = True

                if runnable:
                    wqueues[i].put(sub)
                    wlock.acquire()
                    wset.add(int(sub[0]))
                    wlock.release()
                    break

        time.sleep(1)
        pass
    exit(0)


assert __name__ == "__main__"

with open("_config.yml", "r") as config_file:
    config = yaml.load(config_file.read())
    db_config = config["DATABASE"]
    butler_config = config["BUTLER"]

    # Producer SQL
    db = MySQLdb.connect(
        host=db_config["host"], user=db_config["user"], passwd=db_config["password"], db=db_config["database"]
    )
    cursor = db.cursor()

    # Consumer SQL
    worker_cursor = []
    for i in range(0, len(butler_config)):
        db = MySQLdb.connect(
            host=db_config["host"], user=db_config["user"], passwd=db_config["password"], db=db_config["database"]
        )
        worker_cursor.append(db.cursor())

    # GO
    main(butler_config)
