import MySQLdb

class DB:
    def __init__(self, config):
        db_config = config['DATABASE']
        db = MySQLdb.connect(host=db_config['host'], user=db_config['user'], passwd=db_config['password'], db=db_config['database'])
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
