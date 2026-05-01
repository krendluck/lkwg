import re
import json
import os
import time

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context


@AgentServer.custom_action("AutoReleasePetAction")
class AutoReleasePetAction(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        raw = argv.reco_detail

        detail = ""
        if raw is not None:
            if isinstance(raw.raw_detail, dict):
                detail = raw.raw_detail.get("text", "")
            elif isinstance(raw.raw_detail, str):
                detail = raw.raw_detail
            else:
                detail = str(raw.raw_detail)

        try:
            param = json.loads(argv.custom_action_param or "{}")
        except Exception:
            param = {}
        debug_log = param.get("debug_log", False)

        if debug_log:
            os.makedirs("debug", exist_ok=True)
            with open(os.path.join("debug", "release_log.txt"), "a") as logf:
                logf.write(f"[{time.strftime('%H:%M:%S')}] ACTION detail={detail}\n")

        key_code = 50

        if "not_found" not in detail:
            match = re.search(r'next:(\S+)', detail)
            if match:
                next_action = match.group(1)
                if next_action.isdigit():
                    key_code = 48 + int(next_action)
                elif next_action == "switch":
                    key_code = 50

        context.override_pipeline({"DoReleaseKey": {"key": key_code}})
        return True