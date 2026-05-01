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
        try:
            param = json.loads(argv.custom_action_param or "{}")
        except Exception:
            param = {}

        debug_log = param.get("debug_log", False)
        slots = param.get("slots", [
            [95, 132, 23, 18],
            [95, 186, 23, 18],
            [95, 240, 23, 18],
            [95, 294, 23, 18],
            [95, 348, 23, 18],
        ])
        match_threshold = param.get("match_threshold", 0.7)

        logf = None

        def _log(msg):
            line = f"[{time.strftime('%H:%M:%S')}] {msg}"
            print(line)
            if logf:
                logf.write(line + "\n")
                logf.flush()

        if debug_log:
            os.makedirs("debug", exist_ok=True)
            logf = open(os.path.join("debug", "release_log.txt"), "a")
            _log("=== start ===")

        released_nums = set()

        for i, slot in enumerate(slots):
            pet_num = i + 2
            entry = f"pet{pet_num}_check"

            try:
                context.override_pipeline({
                    entry: {
                        "recognition": "TemplateMatch",
                        "template": "Custom/status.png",
                        "roi": slot,
                        "threshold": match_threshold,
                    }
                })
                match_result = context.run_recognition(entry, argv.image)
            except Exception as e:
                _log(f"pet_{pet_num} EXCEPTION: {e}")
                continue

            hit = match_result is not None and match_result.hit
            _log(f"pet_{pet_num} hit={hit}")

            if hit:
                released_nums.add(pet_num)

        if released_nums:
            unreleased = [n for n in range(2, 7) if n not in released_nums]
            if unreleased:
                next_num = min(unreleased)
                key_code = 48 + next_num
            else:
                next_num = "switch"
                key_code = 50
        else:
            next_num = None
            key_code = 50

        _log(f"released={list(sorted(released_nums))}, next={next_num}, key_code={key_code}")

        controller = context.tasker.controller
        controller.post_click_key(key_code).wait()
        _log(f"pressed key_code={key_code}")

        if logf:
            logf.close()

        return True