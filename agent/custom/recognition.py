from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context

import json
@AgentServer.custom_recognition("AutoLaunch_Check")
class MyRecongition(CustomRecognition):

    # analyze() 是识别器的核心方法，每次 Pipeline 执行到此节点时自动调用。
    #
    # 参数：
    #   context：MAA 上下文对象（见上方导入说明）
    #   argv：识别参数，包含以下字段：
    #     - argv.image：当前截图（numpy.ndarray，BGR 格式）
    #     - argv.custom_recognition_param：Pipeline 中 custom_recognition_param 传入的参数（JSON 字符串）
    #     - argv.node_name：当前 Pipeline 节点名称
    #     - argv.task_detail：当前任务详情
    #     - argv.roi：识别区域
    #
    # 返回值：
    #   CustomRecognition.AnalyzeResult，包含：
    #     - box：识别到的区域坐标 (x, y, w, h)，匹配失败传 None
    #     - detail：识别结果详情，可以是字符串或字典，会传递给对应的 CustomAction
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:

        # argv.custom_recognition_param：从 Pipeline JSON 传入的参数字符串。
        # 在 Pipeline 中这样配置：
        #   "custom_recognition_param": "{\"name\":\"value\"}"
        # 用 json.loads 解析为字典，注意是 custom_recognition_param 不是 custom_action_param
        try:
            param = json.loads(argv.custom_recognition_param or "{}")
        except Exception:
            param = {}

        # 从参数中取出配置项，提供默认值
        # template：模板图片的路径（相对于 resource/image 目录），如 "Custom/Lanuch.png"
        # threshold：模板匹配的相似度阈值，0~1，越大越严格
        # roi：识别区域 [x, y, width, height]，即只在截图的这个矩形区域内做匹配
        threshold = param.get("threshold", 0.7)
        roi = param.get("roi", [544, 496, 192, 85])
        template = param.get("template", "Custom/Lanuch.png")

        # context.run_recognition()：在当前截图中执行指定名称的识别任务。
        # 参数1 "LauchCheck"：Pipeline 任务的名称（可以是已定义的，也可以是临时的）
        # 参数2 argv.image：待识别的截图图像（由 MaaFramework 自动传入的当前画面截图，BGR 格式的 numpy 数组）
        # 参数3 pipeline_override：临时覆盖 Pipeline 配置，仅影响本次调用。
        #   这里定义了一个名为 "LauchCheck" 的临时识别任务：
        #     - "recognition": "TemplateMatch" — 使用模板匹配识别算法
        #     - "template": 模板图片路径 — 用来和截图做对比的图片
        #     - "roi": 识别区域 — 只在截图的指定矩形区域内匹配，提高速度和准确度
        #     - "threshold": 匹配阈值 — 相似度大于此值才算匹配成功
        #   注意：pipeline_override 中必须包含 recognition 字段，否则无法识别
        #   注意：template 和 argv.image 是不同的！template 是模板图片路径，argv.image 是当前截图
        reco_detail = context.run_recognition(
            "LauchCheck",
            argv.image,
            pipeline_override={"LauchCheck": {
                "recognition": "TemplateMatch",
                "template": template,
                "roi": roi,
                "threshold": threshold}},
        )

        # CustomRecognition.AnalyzeResult：识别结果
        #   box：识别到的区域坐标元组 (x, y, w, h)，传 None 表示未识别到
        #   detail：识别结果详情，字符串或字典类型
        #     这个 detail 会被传递给 Pipeline 中对应的 CustomAction，
        #     通过 argv.reco_detail 可以在 Action 中获取到
        return CustomRecognition.AnalyzeResult(
            box=(0, 0, 100, 100), detail="Hello World!"
        )