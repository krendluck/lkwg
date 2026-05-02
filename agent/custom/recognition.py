"""
自动登录检测模块

功能：检测游戏登录界面的"启动"按钮是否仍在屏幕上。
  Pipeline 中 Auto_LaunchEntry 使用 custom_recognition="AutoLaunch_Check" 调用此识别器。
  如果按钮仍在 → 说明登录还没成功，继续等待。
  如果按钮消失 → 说明登录成功，流程结束。

检测方式：在指定 ROI 区域 [544, 496, 192, 85] 模板匹配 Custom/Lanuch.png。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context


@AgentServer.custom_recognition("AutoLaunch_Check")
class AutoLaunchCheckReco(CustomRecognition):

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:

        # 在登录按钮区域检测 Lanuch.png 模板
        # pipeline_override 仅影响本次调用，不会修改全局 pipeline
        reco_detail = context.run_recognition(
            "LauchCheck",
            argv.image,
            pipeline_override={"LauchCheck": {
                "recognition": "TemplateMatch",
                "template": "Custom/Lanuch.png",
                "roi": [544, 496, 192, 85],
            }},
        )

        # 匹配到按钮 → 返回 hit=True，登录按钮还在，继续等待
        # 未匹配到  → 返回 hit=False，登录成功，流程结束
        if reco_detail and reco_detail.hit:
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 100, 100),
                detail="login_button_found",
            )
        else:
            return CustomRecognition.AnalyzeResult(
                box=None,
                detail="login_button_gone",
            )