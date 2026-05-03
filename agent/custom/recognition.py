from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context

import json

_switch_keys = [2, 3, 4, 5, 6]
_switch_key_index = 0


@AgentServer.custom_recognition("AutoLaunch_Check")
class AutoLaunchRecognition(CustomRecognition):

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:

        try:
            param = json.loads(argv.custom_recognition_param or "{}")
        except Exception:
            param = {}

        if "template" not in param:
            raise ValueError("template 参数缺失")
        if "threshold" not in param:
            raise ValueError("threshold 参数缺失")
        if "roi" not in param:
            raise ValueError("roi 参数缺失")

        template = param["template"]
        threshold = param["threshold"]
        roi = param["roi"]

        reco_detail = context.run_recognition(
            "LauchCheck",
            argv.image,
            pipeline_override={"LauchCheck": {
                "recognition": "TemplateMatch",
                "template": template,
                "roi": roi,
                "threshold": threshold,
            }},
        )

        if reco_detail is not None and reco_detail.hit:
            score = 0.0
            if reco_detail.best_result and isinstance(reco_detail.best_result.detail, dict):
                score = reco_detail.best_result.detail.get("score", 0.0)
            return CustomRecognition.AnalyzeResult(
                box=reco_detail.box,
                detail=json.dumps({"hit": True, "score": score, "roi": roi}),
            )
        else:
            return CustomRecognition.AnalyzeResult(
                box=None,
                detail=json.dumps({"hit": False}),
            )


@AgentServer.custom_recognition("AutoReleasePet_recognition")
class AutoReleasePetRecognition(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        global _switch_key_index
        try:
            param = json.loads(argv.custom_recognition_param or "{}")
        except Exception:
            param = {}

        if "template" not in param:
            raise ValueError("template 参数缺失")
        if "threshold" not in param:
            raise ValueError("threshold 参数缺失")
        if "slots" not in param:
            raise ValueError("slots 参数缺失")

        template = param["template"]
        threshold = param["threshold"]
        slots = param["slots"]

        released_nums = set()
        for i, slot in enumerate(slots):
            pet_num = i + 2
            entry = f"pet{pet_num}_check"

            try:
                match_result = context.run_recognition(
                    entry,
                    argv.image,
                    pipeline_override={entry: {
                        "recognition": "TemplateMatch",
                        "template": template,
                        "roi": slot,
                        "threshold": threshold,
                    }},
                )
            except Exception:
                continue

            if match_result is None:
                continue

            if match_result.hit:
                released_nums.add(pet_num)

        if released_nums:
            unreleased = [n for n in range(2, 7) if n not in released_nums]
            if unreleased:
                _switch_key_index = 0
                next_num = min(unreleased)
                key_code = 48 + next_num
            else:
                key_num = _switch_keys[_switch_key_index]
                next_num = key_num
                key_code = 48 + key_num
                _switch_key_index = (_switch_key_index + 1) % len(_switch_keys)
        else:
            return CustomRecognition.AnalyzeResult(
                box=None,
                detail={"next_num": None, "key_code": 0},
            )

        return CustomRecognition.AnalyzeResult(
            box=(0, 0, 1, 1),
            detail={"next_num": next_num, "key_code": key_code},
        )


__all__ = [
    "AutoLaunchRecognition",
    "AutoReleasePetRecognition",
]
