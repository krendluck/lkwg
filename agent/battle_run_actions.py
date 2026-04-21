import json
import random
import time

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction


def _coerce_non_negative_int(name, value, default=0):
    if value in (None, ""):
        return default

    number = int(value)
    if number < 0:
        raise ValueError(f"{name} must be greater than or equal to 0")

    return number


def resolve_wait_seconds(config, randint_func=random.randint):
    mode = str(config.get("mode", "fixed")).strip().lower()

    if mode == "fixed":
        return _coerce_non_negative_int("fixed_seconds", config.get("fixed_seconds"), default=0)

    if mode == "random":
        min_seconds = _coerce_non_negative_int(
            "random_min_seconds",
            config.get("random_min_seconds"),
            default=0,
        )
        max_seconds = _coerce_non_negative_int(
            "random_max_seconds",
            config.get("random_max_seconds"),
            default=0,
        )
        if min_seconds > max_seconds:
            raise ValueError("random_min_seconds must be less than or equal to random_max_seconds")

        return int(randint_func(min_seconds, max_seconds))

    raise ValueError(f"unsupported wait mode: {mode}")


@AgentServer.custom_action("battle_run")
class BattleRunAction(CustomAction):
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        del context

        try:
            payload = json.loads(argv.custom_action_param or "{}")
            seconds = resolve_wait_seconds(payload)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            print(f"battle_run invalid param: {exc}")
            return False

        print(f"battle_run sleeping for {seconds} seconds")
        time.sleep(seconds)
        return True
