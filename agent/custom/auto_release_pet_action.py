import json
import os
import re
import time

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context


@AgentServer.custom_action("AutoReleasePetAction")
class AutoReleasePetAction(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        raw = argv.reco_detail

        if raw is None:
            detail = ""
        elif hasattr(raw, 'raw_detail') and isinstance(raw.raw_detail, dict):
            detail = raw.raw_detail.get("text", "")
        elif hasattr(raw, 'all_results') and raw.all_results:
            r0 = raw.all_results[0]
            d = r0.detail if hasattr(r0, 'detail') else None
            if isinstance(d, dict):
                detail = d.get("text", "")
            elif d is not None:
                detail = str(d).strip('"')
            else:
                detail = ""
        elif hasattr(raw, 'best_result') and raw.best_result:
            d = raw.best_result.detail if hasattr(raw.best_result, 'detail') else None
            if isinstance(d, dict):
                detail = d.get("text", "")
            elif d is not None:
                detail = str(d).strip('"')
            else:
                detail = ""
        elif hasattr(raw, 'raw_detail') and raw.raw_detail is not None:
            detail = str(raw.raw_detail)
        else:
            detail = str(raw)

        logf = None
        def _log(msg):
            line = f"[{time.strftime('%H:%M:%S')}] ACTION {msg}"
            print(line)
            if logf:
                logf.write(line + "\n")
                logf.flush()

        os.makedirs("debug", exist_ok=True)
        logf = open(os.path.join("debug", "release_log.txt"), "a")
        _log(f"raw_type={type(raw).__name__} detail={detail}")

        key_code = 50

        if "not_found" in detail:
            key_code = 50
            _log(f"not_found → key={key_code}")
        elif "in_battle" in detail:
            _log("in_battle, skip")
            logf.close()
            return True
        else:
            match = re.search(r'next:(\S+)', detail)
            if match:
                next_action = match.group(1)
                _log(f"parsed next_action={next_action}")
                if next_action.isdigit():
                    key_code = 48 + int(next_action)
                elif next_action == "switch":
                    key_code = 50
            else:
                _log("no next: match, using default key=50")

        _log(f"override_pipeline DoReleaseKey key={key_code}")
        context.override_pipeline({"DoReleaseKey": {"key": key_code}})
        _log("done")

        logf.close()
        return True
