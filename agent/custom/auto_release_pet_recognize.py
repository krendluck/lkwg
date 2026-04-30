import json
import os
import time
from collections import deque

from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context


@AgentServer.custom_recognition("AutoReleasePetReco")
class AutoReleasePetReco(CustomRecognition):

    _hits = {}

    def analyze(self, context: Context, argv: CustomRecognition.AnalyzeArg) -> CustomRecognition.AnalyzeResult:
        try:
            payload = json.loads(argv.custom_recognition_param or "{}")
        except:
            payload = {}

        debug_log = payload.get("debug_log", False)
        slots = payload.get("slots", [
            [49, 129, 72, 37],
            [49, 185, 71, 33],
            [49, 239, 69, 35],
            [49, 294, 69, 33],
            [49, 349, 64, 34],
        ])
        match_threshold = payload.get("match_threshold", 0.7)
        confirm_window = payload.get("confirm_window", 10)
        confirm_ratio = payload.get("confirm_ratio", 0.7)

        if isinstance(match_threshold, int) and match_threshold > 1:
            match_threshold = match_threshold / 10.0
        if isinstance(confirm_ratio, int) and confirm_ratio > 1:
            confirm_ratio = confirm_ratio / 10.0

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

        for i, slot in enumerate(slots):
            pet_num = i + 2
            entry = f"pet{pet_num}_check"

            try:
                match_result = context.run_recognition(
                    entry,
                    argv.image,
                    {
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

            hit = False
            if match_result:
                box = getattr(match_result, "box", None)
                if box is not None:
                    if hasattr(box, "w"):
                        bw, bh = box.w, box.h
                    else:
                        bw, bh = box[2], box[3]
                    if bw > 0 and bh > 0:
                        hit = True

            if pet_num not in self._hits:
                self._hits[pet_num] = deque(maxlen=confirm_window)
            self._hits[pet_num].append(1 if hit else 0)

            window = self._hits[pet_num]
            window_sum = sum(window)
            window_len = len(window)
            ratio = window_sum / window_len if window_len > 0 else 0.0
            confirmed = window_len >= confirm_window and ratio >= confirm_ratio

            status = "confirmed" if confirmed else ("pending+" if hit else "pending-")
            _log(f"pet_{pet_num} hit={hit} window={window_sum}/{window_len}({ratio:.2f}) [{status}]")

        released_nums = {n for n in range(2, 7)
                         if n in self._hits
                         and len(self._hits[n]) >= confirm_window
                         and sum(self._hits[n]) / len(self._hits[n]) >= confirm_ratio}

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
            box=(0, 0, 0, 0),
            detail=detail,
        )
