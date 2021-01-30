from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn, Optional, Tuple

from judge_common import DB, Config

if TYPE_CHECKING:
    from judge_sender.context import Problem, Result, Submission


class DBAgent:
    def __init__(self, config: Config):
        self.db = DB(config)
        self.next_submission = None

    def has_next_submission(self) -> bool:
        row = self.db.get_next_submission_to_judge()

        if row == None:
            return False

        self.next_submission = row

        return True

    def get_next_submission(self) -> Optional[Tuple[str, str, int]]:
        if self.next_submission is None:
            return None

        return self.next_submission

    def update_submission(self, sid: str, result: Result) -> NoReturn:
        self.db.update_submission(result.score, result.status_code, result.cpu, result.mem, sid)

        return
