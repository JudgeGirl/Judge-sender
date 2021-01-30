class Result:
    @property
    def status_code(self):
        return self._status_code

    @status_code.setter
    def status_code(self, v):
        self._status_code = v

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, v):
        self._description = v

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, v):
        self._score = v

    @property
    def cpu(self):
        return self._cpu

    @cpu.setter
    def cpu(self, v):
        self._cpu = v

    @property
    def mem(self):
        return self._mem

    @mem.setter
    def mem(self, v):
        self._mem = v
