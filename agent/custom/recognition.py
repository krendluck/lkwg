from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context

import json
import os
import time
import numpy as np


def _log(msg):
    os.makedirs("debug", exist_ok=True)
    with open(os.path.join("debug", "release_log.txt"), "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")


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

        # ====== 1. 检查截图 ======
        image = argv.image
        if image is None:
            _log("Reco 错误: argv.image 为 None")
        elif isinstance(image, np.ndarray):
            _log(f"Reco 截图信息: shape={image.shape}, dtype={image.dtype}, size={image.size}")
        else:
            _log(f"Reco 截图信息: type={type(image).__name__}")

        # ====== 2. 解析参数 ======
        try:
            raw_param = argv.custom_recognition_param or "{}"
            param = json.loads(raw_param)
        except Exception as e:
            _log(f"Reco 参数解析失败: {e}")
            param = {}

        _log(f"Reco 开始, 收到参数: {param}")

        if "template" not in param:
            _log("Reco 错误: template 参数缺失")
            raise ValueError("template 参数缺失")
        if "threshold" not in param:
            _log("Reco 错误: threshold 参数缺失")
            raise ValueError("threshold 参数缺失")
        if "slots" not in param:
            _log("Reco 错误: slots 参数缺失")
            raise ValueError("slots 参数缺失")

        template = param["template"]
        threshold = param["threshold"]
        slots = param["slots"]

        _log(f"Reco 参数解析完毕: template={template}, threshold={threshold}, slots数量={len(slots)}")

        # ====== 3. 检查模板文件 ======
        template_path = os.path.join("assets", template)
        if os.path.exists(template_path):
            _log(f"Reco 模板文件存在: {template_path}")
        else:
            _log(f"Reco 模板文件不存在: {template_path}")

        # ====== 4. 遍历每个槽位 ======
        released_nums = set()
        for i, slot in enumerate(slots):
            pet_num = i + 2
            entry = f"pet{pet_num}_check"

            _log(f"pet_{pet_num} 开始识别: roi={slot}")

            try:
                match_result = context.run_recognition(
                    entry,
                    image,
                    pipeline_override={entry: {
                        "recognition": "TemplateMatch",
                        "template": template,
                        "roi": slot,
                        "threshold": threshold,
                    }},
                )
            except Exception as e:
                _log(f"pet_{pet_num} 识别异常: {e}")
                continue

            if match_result is None:
                _log(f"pet_{pet_num} match_result 为 None")
                continue

            hit = match_result.hit
            _log(f"pet_{pet_num} match_result: hit={hit}, box={match_result.box}, best_detail={match_result.best_result.detail if match_result.best_result else 'None'}")

            if hit:
                released_nums.add(pet_num)

        _log(f"Reco 循环结束: released_nums={sorted(released_nums)}")

        # ====== 5. 计算结果 ======
        if released_nums:
            unreleased = [n for n in range(2, 7) if n not in released_nums]
            if unreleased:
                next_num = min(unreleased)
                key_code = 48 + next_num
            else:
                next_num = -1
                key_code = 50
        else:
            _log("Reco 结果: 无已释放槽位")
            return CustomRecognition.AnalyzeResult(
                box=None,
                detail="None,0",
            )

        detail_str = f"{next_num},{key_code}"
        _log(f"Reco 结果: released={sorted(released_nums)} unreleased={unreleased} next_num={next_num} key_code={key_code} detail_str={detail_str}")

        return CustomRecognition.AnalyzeResult(
            box=(0, 0, 1, 1),
            detail=detail_str,
        )


__all__ = [
    "AutoLaunchRecognition",
    "AutoReleasePetRecognition",
]