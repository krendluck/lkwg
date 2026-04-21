import os
import re
import sys
from pathlib import Path

from maa.agent.agent_server import AgentServer
from maa.toolkit import Toolkit

import agent.battle_run_actions as battle_run_actions
import my_reco


def _write_boot_log(message: str) -> None:
    try:
        project_dir = Path(__file__).resolve().parent.parent
        debug_dir = project_dir / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        log_file = debug_dir / "agent_boot.log"
        with log_file.open("a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception:
        # Never let diagnostics break agent startup.
        pass


def _is_valid_identifier(value: str) -> bool:
    if not value:
        return False
    # Maa may use UUID-like IPC id or numeric TCP port as identifier.
    if value.isdigit():
        return True
    return re.fullmatch(r"[0-9a-fA-F-]{32,64}", value) is not None


def _resolve_identifier() -> str | None:
    # 1) Try command-line arguments first.
    for arg in reversed(sys.argv[1:]):
        if _is_valid_identifier(arg):
            return arg

    # 2) Fallback to common environment variable names.
    env_keys = [
        "PI_CLIENT_AGENT_IDENTIFIER",
        "PI_AGENT_IDENTIFIER",
        "PI_CLIENT_IDENTIFIER",
        "PI_IDENTIFIER",
        "AGENT_IDENTIFIER",
        "MAA_AGENT_IDENTIFIER",
    ]
    for key in env_keys:
        value = os.environ.get(key, "").strip()
        if _is_valid_identifier(value):
            return value

    # 3) Keep old behavior as final fallback.
    if len(sys.argv) >= 2:
        return sys.argv[-1]

    return None


def main():
    Toolkit.init_option("./")
    socket_id = _resolve_identifier()

    _write_boot_log(
        f"cwd={os.getcwd()} argv={sys.argv} resolved_identifier={socket_id!r}"
    )

    if not socket_id:
        print("Failed to resolve agent identifier.")
        print("Expected in argv or PI_* / *_AGENT_IDENTIFIER environment variable.")
        sys.exit(1)

    AgentServer.start_up(socket_id)
    AgentServer.join()
    AgentServer.shut_down()


if __name__ == "__main__":
    main()
