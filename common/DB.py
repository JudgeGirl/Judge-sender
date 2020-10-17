import MySQLdb

class DB:
    def __init__(self, host, user, password, db_name):
        db = MySQLdb.connect(host=host, user=user, passwd=password, db=db_name)
        self.db = db
        self.cursor = db.cursor()

    def write_report(self, sid, content):
        query = 'INSERT INTO reports (sid, content) VALUES ({}, "{}")'.format(sid, content)
        self.cursor.execute(query)
        self.db.commit()

    def get_cursor(self):
        return self.cursor

    def get_next_submission_to_judge(self):
        query = 'SELECT sid, pid, lng FROM submissions WHERE res = 0 ORDER BY sid LIMIT 1'
        self.cursor.execute(query)
        result = self.cursor.fetchone()

        if not result:
            return None

        return map(int, result)

    def update_submission(self, scr, res, cpu, mem, sid):
        query = 'UPDATE submissions SET scr = {}, res = {}, cpu={}, mem={} WHERE sid={}'.format(
            scr,
            res,
            cpu,
            mem,
            sid
        )
        self.cursor.execute(query)
        self.db.commit()
