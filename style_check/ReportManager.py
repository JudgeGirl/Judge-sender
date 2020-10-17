import os.path

class ReportManager:
    def __init__(self):
        self.content = ''

    def add_report(self, target_source_code, content):
        self.add_lines('File: ' + target_source_code)
        self.add_lines(content)

    def add_lines(self, lines):
        self.content += lines + '\n'

    def get_report(self):
        return self.content
