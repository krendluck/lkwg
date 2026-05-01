import json
import os
import time

from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context


@AgentServer.custom_recognition("AutoReleasePetReco")
class AutoReleasePetReco(CustomRecognition):

    def analyze(self, context: Context, argv: CustomRecognition.AnalyzeArg) -> CustomRecognition.AnalyzeResult:
        try:
            payload = json.loads(argv.custom_recognition_param or "{}")
        except Exception:
            payload = {}

        debug_log = payload.get("debug_log", False)
        slots = payload.get("slots", [
            [95, 132, 23, 18],
            [95, 186, 23, 18],
            [95, 240, 23, 18],
            [95, 294, 23, 18],
            [95, 348, 23, 18],
        ])
        match_threshold = payload.get("match_threshold", 0.7)

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
                reco_detail = context.run_recognition(
                    entry,
                    argv.image,
                    pipeline_override={
                        entry: {
                            "recognition": "TemplateMatch",
                            "template": "Custom/status.png",
                            "roi": slot,
                            "threshold": match_threshold,
                        }
                    },
                )
            except Exception as e:
                _log(f"pet_{pet_num} EXCEPTION: {e}")
                continue

            hit = reco_detail is not None and reco_detail.hit
            _log(f"pet_{pet_num} hit={hit}")

            if hit:
                released_nums.add(pet_num)

        if released_nums:
            unreleased = [n for n in range(2, 7) if n not in released_nums]
            if unreleased:
                next_num = min(unreleased)
                detail = f"released:{list(sorted(released_nums))},next:{next_num}"
            else:
                detail = f"released:{list(sorted(released_nums))},next:switch"
        else:
            detail = "not_found"

        _log(f"=> {detail}")

        if logf:
            logf.close()

        return CustomRecognition.AnalyzeResult(
            box=(0, 0, 1, 1),
            detail={"text": detail},
        )