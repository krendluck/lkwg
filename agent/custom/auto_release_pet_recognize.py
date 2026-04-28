import json
import re

from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context


@AgentServer.custom_recognition("AutoReleasePetReco")
class AutoReleasePetReco(CustomRecognition):
    def analyze(self, context: Context, argv: CustomRecognition.AnalyzeArg) -> CustomRecognition.AnalyzeResult:
        try:
            payload = json.loads(argv.custom_recognition_param or "{}")
        except:
            payload = {}
        
        roi = payload.get("roi", [72, 123, 90, 402])
        threshold = payload.get("threshold", 0.3)
        count = payload.get("count", 5)
        battle_roi = payload.get("battle_roi", [920, 613, 91, 92])
        battle_threshold = payload.get("battle_threshold", 0.8)

        battle_result = context.run_recognition(
            "TemplateMatch",
            argv.image,
            {
                "TemplateMatch": {
                    "template": "Battle/ESC.png",
                    "roi": battle_roi,
                    "threshold": battle_threshold
                }
            }
        )

        if battle_result and battle_result.box:
            return CustomRecognition.AnalyzeResult(
                box=None,
                detail="in_battle"
            )

        template_result = context.run_recognition(
            "TemplateMatch",
            argv.image,
            {
                "TemplateMatch": {
                    "template": "Custom/status.png",
                    "roi": roi,
                    "threshold": threshold,
                    "count": count
                }
            }
        )

        if not template_result or not template_result.box:
            return CustomRecognition.AnalyzeResult(box=None, detail="not_found")

        released_nums = set()

        for box in template_result.box:
            if len(box) >= 4:
                bx, by, bw, bh = box[0], box[1], box[2], box[3]
                center_x = bx + bw // 2
                center_y = by + bh // 2

                num_box_x = center_x - 64
                num_box_y = center_y + 8
                num_box_w = 24
                num_box_h = 25

                ocr_result = context.run_recognition(
                    "OCR",
                    argv.image,
                    {
                        "OCR": {
                            "roi": [num_box_x, num_box_y, num_box_w, num_box_h]
                        }
                    }
                )

                if ocr_result and ocr_result.detail:
                    text = str(ocr_result.detail)
                    digits = re.sub(r'\D', '', text)
                    if digits:
                        num = int(digits[0])
                        released_nums.add(num)

        unreleased = [n for n in range(2, 7) if n not in released_nums]

        if unreleased:
            next_num = min(unreleased)
            detail = f"released:{list(released_nums)},next:{next_num}"
        else:
            detail = f"released:{list(released_nums)},next:switch"

        bx, by, bw, bh = template_result.box[0][0], template_result.box[0][1], template_result.box[0][2], template_result.box[0][3]
        return CustomRecognition.AnalyzeResult(
            box=(bx, by, bw, bh),
            detail=detail
        )