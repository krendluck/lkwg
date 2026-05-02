# agent/custom/__init__.py
# 导入所有自定义模块，确保 @AgentServer 装饰器触发注册
from .actions import *
from .auto_release_pet import *
from .mouse_long_press_action import *
from .recognition import *