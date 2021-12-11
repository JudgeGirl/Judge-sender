from __future__ import annotations

import binascii
import os
import subprocess
from typing import TYPE_CHECKING, NoReturn, Optional

from judge_sender.context import Context, Result

if TYPE_CHECKING:
    from judge_sender.context import Judger


class ReceiverAgent:
    def __init__(self, judger: Judger):
        judger_user: str = f"{judger.user}@{judger.host}"

        popen_obj = subprocess.Popen(
            ["ssh", judger_user, "export PATH=$PATH:/home/butler; butler"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        self.input_pipe = popen_obj.stdout
        self.output_pipe = popen_obj.stdin

    def read_result(self, context: Context) -> Result:
        result: Result = context.result

        result.score = int(self._read_line())
        result.status_code = int(self._read_line())
        result.cpu = int(self._read_line())
        result.mem = int(self._read_line())
        result.description = self._read_all()

        return result

    def get_next_additional_file(self) -> Optional[str]:
        n: int = int(self.input_pipe.read(2))
        if n <= 0:
            return None

        additional_file = self.input_pipe.read(n).decode()

        return additional_file

    def send_file(self, source_file: str, new_name: str) -> NoReturn:
        """

        Args:
            source_file: The file or directory which we deliver to the receiver in hex string.
            new_name: The name which we rename the source file to.

        """

        assert (
            os.system(
                "cd /run/shm; ln -s '{}' '{}'; tar ch '{}' | gzip -1 > judge_server.tgz".format(
                    os.path.realpath(source_file), new_name, new_name
                )
            )
            == 0
        )
        with open("/run/shm/judge_server.tgz", "rb") as opened_file:
            binary_data = opened_file.read()

        os.remove("/run/shm/{}".format(new_name))
        os.remove("/run/shm/judge_server.tgz")
        hex_data = binascii.hexlify(binary_data)
        self.output_pipe.write(("%10d" % len(hex_data)).encode())
        self.output_pipe.write(hex_data)
        self.output_pipe.flush()

    def end_prepare(self, language) -> None:
        self.output_pipe.write(("%10d" % -language).encode())
        self.output_pipe.flush()

    def _read_line(self):
        return self.input_pipe.readline()

    def _read_all(self):
        return self.input_pipe.read()
