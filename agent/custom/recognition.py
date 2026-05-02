# MaaFramework Agent 自定义识别器模块
# 自定义识别器（CustomRecognition）用于在 Pipeline 中执行自定义的图像识别逻辑。
# 当 Pipeline 任务的 recognition 字段设为 "Custom" 并指定 custom_recognition 名称时，
# MaaFramework 会调用对应注册的识别器类的 analyze() 方法。

# AgentServer：MAA Agent 服务端，用于注册自定义识别器/动作，使其在 Pipeline 中可用
from maa.agent.agent_server import AgentServer
# CustomRecognition：自定义识别器基类，继承它并实现 analyze() 方法即可创建识别器
from maa.custom_recognition import CustomRecognition
# Context：MAA 上下文对象，提供运行时能力：
#   - context.run_recognition()：调用其他 Pipeline 识别任务
#   - context.override_pipeline()：覆盖 Pipeline 配置（影响整个任务后续调用）
#   - context.clone()：克隆上下文，克隆后的修改不影响原始上下文
#   - context.override_next()：动态修改当前节点的下一步跳转
#   - context.tasker.controller：获取控制器，用于发送点击/按键等操作
from maa.context import Context


# @AgentServer.custom_recognition("name") 装饰器：
# 将这个类注册为名为 "AutoLaunch_Check" 的自定义识别器。
# 在 Pipeline JSON 中通过 "custom_recognition": "AutoLaunch_Check" 引用此识别器。
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

        # context.run_recognition()：在当前截图中执行指定名称的识别任务。
        # 参数1 "LauchCheck"：Pipeline 任务的名称（可以是已定义的，也可以是临时的）
        # 参数2 argv.image：待识别的截图图像（由 MaaFramework 自动传入）
        # 参数3 pipeline_override：临时覆盖 Pipeline 配置，仅影响本次调用。
        #   这里定义了一个名为 "LauchCheck" 的临时任务：
        #     - "roi": [544, 496, 192, 85] — 在截图的 (544,496) 位置，192x85 像素区域内匹配
        #   注意：LauchCheck 的 template 字段需要在 Pipeline 中已定义，
        #         或者在 pipeline_override 中一并指定 "template" 和 "recognition"
        reco_detail = context.run_recognition(
            "LauchCheck",
            argv.image,
            pipeline_override={"LauchCheck": {
                "roi": [544,496,192,85]}},
        )

        # context.override_pipeline()：覆盖 Pipeline 配置（影响整个任务的后续调用）。
        # 与 pipeline_override 参数不同，这里修改的是 context 引用本身，
        # 后续所有通过这个 context 执行的识别/动作都会使用这个覆盖后的配置。
        # 注意：如果只想临时修改不影响其他调用，应使用 context.clone()（见下方）
        context.override_pipeline({"MyCustomOCR": {"roi": [1, 1, 114, 514]}})
        # context.run_recognition(...)  # 使用覆盖后的配置执行识别

        # context.clone()：克隆当前上下文，克隆出来的新上下文是独立的。
        # 在新上下文上的 override_pipeline 修改不会影响原始 context。
        # 适用于：需要临时修改配置做一次识别，但不希望影响后续流程的场景。
        new_context = context.clone()
        new_context.override_pipeline({"MyCustomOCR": {"roi": [100, 200, 300, 400]}})
        # 使用克隆的上下文执行识别，识别结果不影响原始 context 的 Pipeline 配置
        reco_detail = new_context.run_recognition("MyCustomOCR", argv.image)

        # context.tasker.controller：获取 MAA 控制器，用于操作游戏窗口。
        # post_click(x, y)：在 (x, y) 坐标处点击（异步操作）。
        # .wait()：等待点击操作完成。
        # 此外还有 post_click_key(key)、post_touch_down/up() 等方法。
        click_job = context.tasker.controller.post_click(10, 20)
        click_job.wait()

        # context.override_next()：动态修改当前节点的下一步跳转。
        # 参数1 argv.node_name：当前节点名称
        # 参数2 ["TaskA", "TaskB"]：替换原 Pipeline 中定义的 next 列表。
        #   执行后，当前节点完成后的下一步不再按 Pipeline 原定义流转，
        #   而是跳转到 "TaskA" 或 "TaskB"（按识别结果选择）。
        context.override_next(argv.node_name, ["TaskA", "TaskB"])

        # CustomRecognition.AnalyzeResult：识别结果
        #   box：识别到的区域坐标元组 (x, y, w, h)，传 None 表示未识别到
        #   detail：识别结果详情，字符串或字典类型
        #     这个 detail 会被传递给 Pipeline 中对应的 CustomAction，
        #     通过 argv.reco_detail 可以在 Action 中获取到
        return CustomRecognition.AnalyzeResult(
            box=(0, 0, 100, 100), detail="Hello World!"
        )