from __future__ import annotations

from typing import TYPE_CHECKING, List
import json
from pathlib import Path
from judge_common import Logger

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

    def get_submission_file_list(self) -> List[List[str]]:
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
                    if submission_file.strip() == "":
                        continue

                    source_file = "{}/{}-{}".format(self.submission_dir, self.submission.sid, i)
                    source_name = submission_file[:-1]
                    submission_file_list.append([source_file, source_name])

                    i += 1

        self.submission_file_list = submission_file_list
        return submission_file_list

    def get_provided_file_list(self) -> List[List[str]]:
        if self.provided_file_list:
            return self.provided_file_list

        provided_file_list = []
        try:
            with open("{}/{}/send.lst".format(self.testdata_dir, self.problem.pid)) as list_file:
                for provided_file in list_file.readlines():
                    if provided_file.strip() == "":
                        continue

                    source_name = provided_file[:-1]
                    source_file = "{}/{}/{}".format(self.testdata_dir, self.problem.pid, source_name)
                    provided_file_list.append([source_file, source_name])

        except:
            pass

        self.provided_file_list = provided_file_list
        return provided_file_list

    def get_common_script_list(self) -> List[List[str]]:
        if self.common_script_list:
            return self.common_script_list

        return [["./const.py", "const.py"], ["{}/{}/judge".format(self.testdata_dir, self.problem.pid), "judge"]]

    def get_full_send_list(self) -> List[List[str]]:
        return self.get_submission_file_list() + self.get_provided_file_list() + self.get_common_script_list()

    def get_additional_file_path(self, file_name):
        return "{}/{}/{}".format(self.testdata_dir, self.problem.pid, file_name)

    def get_compile_args(self) -> List[List[str]]:
        testdata_dir = Path(self.testdata_dir)
        compile_args_file = testdata_dir / str(self.problem.pid) / "compile_arguments.json"

        if not compile_args_file.exists() or not compile_args_file.is_file():
            return []

        try:
            with open(compile_args_file, "r") as f:
                compile_args = json.load(f)
        except Exception as e:
            Logger.warn("failed to read compile arguments from compile_arguments.json")
            Logger.warn(repr(e))

            compile_args = []

        return compile_args


class FileCollectorFactory:
    def __init__(self, testdata_dir: str, submission_dir: str):
        self.testdata_dir = testdata_dir
        self.submission_dir = submission_dir

    def create_file_collector(self, problem: Problem, submission: Submission) -> FileCollector:
        return FileCollector(self.testdata_dir, self.submission_dir, problem, submission)
