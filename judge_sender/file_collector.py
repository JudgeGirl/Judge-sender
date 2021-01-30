from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from judge_sender.context import Problem, Submission


class FileCollector:
    def __init__(self, testdata_dir: str, submission_dir: str, problem: Problem, submission: Submission):
        self.testdata_dir = testdata_dir
        self.submission_dir = submission_dir
        self.problem = problem
        self.submission = submission

        self.submission_file_list = None
        self.provided_file_list = None
        self.common_script_list = None

    def get_submission_file_list(self) -> list[list[str]]:
        if self.submission_file_list:
            return self.submission_file_list

        submission_file_list = []
        if self.problem.language != 0:
            source_file = "{}/{}-0".format(self.submission_dir, self.submission.sid)
            source_name = "source"  # Default name of source file. It should change if we allow other language.

            submission_file_list.append([source_file, source_name])
        else:
            with open("{}/{}/source.lst".format(self.testdata_dir, self.problem.pid)) as list_file:
                i = 0
                for submission_file in list_file.readlines():
                    source_file = "{}/{}-{}".format(self.submission_dir, self.submission.sid, i)
                    source_name = submission_file[:-1]
                    submission_file_list.append([source_file, source_name])

                    i += 1

        self.submission_file_list = submission_file_list
        return submission_file_list

    def get_provided_file_list(self) -> list[list[str]]:
        if self.provided_file_list:
            return self.provided_file_list

        provided_file_list = []
        try:
            with open("{}/{}/send.lst".format(self.testdata_dir, self.problem.pid)) as list_file:
                for provided_file in list_file.readlines():
                    source_name = provided_file[:-1]
                    source_file = "{}/{}/{}".format(self.testdata_dir, self.problem.pid, source_name)
                    provided_file_list.append([source_file, source_name])

        except:
            pass

        self.provided_file_list = provided_file_list
        return provided_file_list

    def get_common_script_list(self) -> list[list[str]]:
        if self.common_script_list:
            return self.common_script_list

        return [["./const.py", "const.py"], ["{}/{}/judge".format(self.testdata_dir, self.problem.pid), "judge"]]

    def get_full_send_list(self) -> list[list[str]]:
        return self.get_submission_file_list() + self.get_provided_file_list() + self.get_common_script_list()

    def get_additional_file_path(self, file_name):
        return "{}/{}/{}".format(self.testdata_dir, self.problem.pid, file_name)
