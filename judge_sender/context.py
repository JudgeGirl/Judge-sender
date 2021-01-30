class Result:
    def __init__(self):
        self.status_code = None
        self.description = None
        self.score = None
        self.cpu = None
        self.mem = None


class Judger:
    def __init__(self, host, user):
        self.host = host
        self.user = user


class Problem:
    def __init__(self, pid, language):
        self.pid = pid
        self.language = language


class Submission:
    def __init__(self, sid):
        self.sid = sid


class Context:
    def __init__(self, problem: Problem, submission: Submission, judger: Judger, config):
        self.problem = problem
        self.submission = submission
        self.judger = judger
        self.result = None
        self.config = config
