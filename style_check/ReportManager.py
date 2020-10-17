import os.path

class ReportManager:
    def __init__(self, report_dierectory):
        self.report_dierectory = report_dierectory

    def init_report(self, report_name):
        report_file_name = self.get_report_filename(report_name)
        if os.path.isfile(report_file_name):
            os.remove(report_file_name)

    def write_report(self, report_name, target_source_code, content):
        self.write_report_file(report_name, 'File: ' + target_source_code + '\n')
        self.write_report_file(report_name, content)

    def write_report_file(self, report_name, data):
        report_filename = self.get_report_filename(report_name)
        try:
            with open(report_filename, 'a') as f:
                f.write(data + '\n')
        except:
            print('error on writing file')

    def get_report_filename(self, report_name):
        return self.report_dierectory + '/' + report_name + ".txt"
