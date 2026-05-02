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

        # 从参数中取出配置项，三个参数都必须在 Pipeline 的 custom_recognition_param 中指定
        # template：模板图片的路径（相对于 resource/image 目录），如 "Custom/Lanuch.png"
        # threshold：模板匹配的相似度阈值，0~1，越大越严格
        # roi：识别区域 [x, y, width, height]，即只在截图的这个矩形区域内做匹配
        if "template" not in param:
            raise ValueError("template 参数缺失，请在 custom_recognition_param 中指定模板图片路径，例如 \"template\": \"Custom/Lanuch.png\"")
        if "threshold" not in param:
            raise ValueError("threshold 参数缺失，请在 custom_recognition_param 中指定匹配阈值，例如 \"threshold\": 0.7")
        if "roi" not in param:
            raise ValueError("roi 参数缺失，请在 custom_recognition_param 中指定识别区域，例如 \"roi\": [544, 496, 192, 85]")
        template = param["template"]
        threshold = param["threshold"]
        roi = param["roi"]

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

        # reco_detail 是 context.run_recognition() 的返回值，类型为 RecognitionDetail
        # 关键字段：
        #   .hit：bool — 是否匹配成功，True=匹配到，False=没匹配到
        #   .box：Rect 或 None — 匹配到的区域坐标 (x, y, w, h)，未匹配到时为 None
        #   .best_result：RecognitionResult 或 None — 最佳匹配结果
        #     .best_result.detail：dict — 识别详情，模板匹配时包含 score 等信息
        #   .raw_detail：dict — 原始识别详情

        # 判断是否匹配成功
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
class MyRecongition(CustomRecognition):        
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
            pet_num = i + 2  # 槽位索引0对应宠物2
            entry = f"pet{pet_num}_check"

            try:
                # 动态创建一个 TemplateMatch 识别任务，指定 ROI 和阈值
                # override_pipeline 会临时添加/覆盖 pipeline 中的任务定义
                context.override_pipeline({
                    entry: {
                        "recognition": "TemplateMatch",
                        "template": template,
                        "roi": slot,
                        "threshold": threshold,
                    }
                })
                # 用当前截图执行识别，返回匹配结果
                match_result = context.run_recognition(entry, argv.image)
            except Exception as e:
                continue

            # hit=True 表示在该区域匹配到了 status.png 模板，即此槽位宠物已释放
            hit = match_result is not None and match_result.hit

            if hit:
                released_nums.add(pet_num)

        # 根据检测结果决定要按哪个键
        if released_nums:
            unreleased = [n for n in range(2, 7) if n not in released_nums]
            if unreleased:
                # 有未释放的槽位 → 选编号最小的，按对应数字键放入宠物
                next_num = min(unreleased)
                key_code = 48 + next_num  # 数字键VK码: '2'=50, '3'=51, ...
            else:
                # 所有槽位都已释放 → 按数字键2切换到下一页继续放宠
                next_num = "switch"
                key_code = 50  # 数字键2
        else:
            # 没检测到任何已释放槽位 → 按数字键2（默认操作/切换页面）
            next_num = None
            key_code = 50  # 数字键2

        # detail 必须是字符串类型，Agent IPC 模式下 dict 类型会丢失
        # 用 JSON 字符串传递多个值，Action 端用 json.loads 解析
        detail_str = json.dumps({"next_num": next_num, "key_code": key_code})

        return CustomRecognition.AnalyzeResult(
                box=(0, 0, 1, 1),
                detail=detail_str,
            )