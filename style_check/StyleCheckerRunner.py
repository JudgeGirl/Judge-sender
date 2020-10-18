import os
from shutil import copyfile
import subprocess
import os.path

class StyleCheckerRunner:
    source_name = "source"

    def check_report(self, checker_executable, code):
        # create local compilable
        compilable = self.get_compilable(code.language_extension)
        copyfile(code.source_file, compilable)

        # run checker
        process = subprocess.Popen([checker_executable, compilable], stdout=subprocess.PIPE)
        process.wait()
        report = process.stdout.read()

        # clean up
        self.try_delete("a.out")
        self.try_delete(compilable)

        return report.decode('utf-8')

    def get_compilable(self, extenstion):
        return './{}.{}'.format(self.source_name, extenstion)

    def init_report(self, report_filename):
        report_file = '{}/{}'.format(self.report_directory, report_filename)
        if os.path.isfile(report_file):
            os.remove(report_file)

    def try_delete(self, filename):
        try:
            os.remove(filename)
        except FileNotFoundError as e:
            print(e)
