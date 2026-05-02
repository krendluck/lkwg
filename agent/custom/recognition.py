from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context

import json

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
            raise ValueError("template 参数缺失，请在 custom_recognition_param 中指定模板图片路径，例如 \"template\": \"Custom/Lanuch.png\"")
        if "threshold" not in param:
            raise ValueError("threshold 参数缺失，请在 custom_recognition_param 中指定匹配阈值，例如 \"threshold\": 0.7")
        if "roi" not in param:
            raise ValueError("roi 参数缺失，请在 custom_recognition_param 中指定识别区域，例如 \"roi\": [544, 496, 192, 85]")
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
                "threshold": threshold}},
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

        try:
            param = json.loads(argv.custom_recognition_param or "{}")
        except Exception:
            param = {}

        if "template" not in param:
            raise ValueError("template 参数缺失，请在 custom_recognition_param 中指定模板图片路径，例如 \"template\": \"Custom/Lanuch.png\"")
        if "threshold" not in param:
            raise ValueError("threshold 参数缺失，请在 custom_recognition_param 中指定匹配阈值，例如 \"threshold\": 0.7")
        if "slots" not in param:
            raise ValueError("slots 参数缺失，请在 custom_recognition_param 中指定识别区域，例如 \"slots\": [[544, 496, 192, 85]]")
        template = param["template"]
        threshold = param["threshold"]
        slots = param["slots"]

        released_nums = set()
        for i, slot in enumerate(slots):
            pet_num = i + 2
            entry = f"pet{pet_num}_check"

            try:
                context.override_pipeline({
                    entry: {
                        "recognition": "TemplateMatch",
                        "template": template,
                        "roi": slot,
                        "threshold": threshold,
                    }
                })
                match_result = context.run_recognition(entry, argv.image)
            except Exception:
                continue

            hit = match_result is not None and match_result.hit

            if hit:
                released_nums.add(pet_num)

        if released_nums:
            unreleased = [n for n in range(2, 7) if n not in released_nums]
            if unreleased:
                next_num = min(unreleased)
                key_code = 48 + next_num
            else:
                next_num = -1
                key_code = 50
        else:
            return CustomRecognition.AnalyzeResult(
                box=None,
                detail=json.dumps({"next_num": None, "key_code": 0}),
            )

        detail_str = json.dumps({"next_num": next_num, "key_code": key_code})

        return CustomRecognition.AnalyzeResult(
                box=(0, 0, 1, 1),
                detail=detail_str,
            )

__all__ = [
    "AutoLaunchRecognition",
    "AutoReleasePetRecognition",
]