from __future__ import annotations
from typing import TYPE_CHECKING

from .const import const
from judge_common import CodePackSerializer, Logger, WorkQueueSender


if TYPE_CHECKING:
    from judge_common import CodePack

status_to_style_check = [const.CE, const.OLE, const.MLE, const.RE, const.TLE, const.WA, const.AC, const.PE]


class StyleCheckHandler:
    def __init__(self, config):
        self.config = config
        self.enabled = config["STYLE_CHECK"]["enabled"]

        if self.enabled:
            self.work_queue_sender = WorkQueueSender(config["RBMQ"]["host"], "style_check_task")
            self.serializer = CodePackSerializer()

        self.heartbeat_threshold = 5
        self.heartbeat_count = 0

    def handle(self, code_pack: CodePack, language: int, result_status: int):
        config = self.config

        if not self.enabled:
            return

        if result_status not in status_to_style_check:
            Logger.info("invalid result status")
            return

        for retry in range(5):
            try:
                code_pack_str = self.serializer.serialize(code_pack)
                self.work_queue_sender.send(code_pack_str)

            except Exception as e:
                Logger.error("failed to send code pack({})".format(retry))
                Logger.error(e)

                # renew WorkQueueSender
                self.work_queue_sender = WorkQueueSender(self.config["RBMQ"]["host"], "style_check_task")
            else:
                break
        else:
            raise Exception("exceed tetry limit")

        return

    def send_heartbeat(self):
        self.heartbeat_count += 1

        if self.heartbeat_count % self.heartbeat_threshold == 0:
            self.work_queue_sender.send_heartbeat()
