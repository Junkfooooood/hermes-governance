"""Test script: invoke governance chain directly without Hermes CLI."""

import json
import os
import sys

# Ensure .env is loaded
env_path = os.path.expanduser("~/.hermes/.env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

# Add hermes-agent to path
hermes_agent_dir = os.path.expanduser("~/.hermes/hermes-agent")
if hermes_agent_dir not in sys.path:
    sys.path.insert(0, hermes_agent_dir)

# Add plugins to path
plugins_dir = os.path.expanduser("~/.hermes/plugins")
if plugins_dir not in sys.path:
    sys.path.insert(0, plugins_dir)

# Load config
from hermes_cli.config import load_config

config = load_config()

# Import governance components directly
from governance.resident_manager import ResidentAgentManager
from governance.ministry_router import MinistryRouter
from governance.state_machine import GovernanceStateMachine
from governance.event_bus import get_bus

# Wire event bus
bus = get_bus()

# Build task
GOAL = """做一个会议纪要网页应用，要求：
1. 通过麦克风收录语音（Web Audio API / MediaRecorder）
2. 语音转文字（可用 Web Speech API 或 Whisper）
3. 将转写的文字通过 AI 进行总结复盘，输出结构化的会议纪要
4. 界面简洁美观，支持导出

技术栈：单页 HTML + JavaScript，不需要后端，可选调用外部 API。"""

CONTEXT = """这是一个测试任务，用于验证三省六部治理链的完整流程。
产出物是一个可以直接在浏览器中打开的 HTML 文件。"""

PRIORITY = "normal"


def run():
    print("=" * 60)
    print("三省六部治理链 — 测试执行")
    print("=" * 60)
    print(f"目标: {GOAL[:80]}...")
    print(f"优先级: {PRIORITY}")
    print()

    # Initialize components
    governance_config = config.get("governance", {})
    manager = ResidentAgentManager(config=config)
    manager.initialize()
    router = MinistryRouter()

    # Create state machine with event callback
    def on_event(txn_id, event_type, payload):
        bus.emit(txn_id, event_type, payload)
        print(f"  [EVENT] {event_type}: {json.dumps(payload, ensure_ascii=False)[:120]}")

    sm = GovernanceStateMachine(manager, router, event_callback=on_event)

    # Create transaction
    txn = sm.create_transaction(GOAL, CONTEXT, PRIORITY)
    print(f"\n事务已创建: {txn.transaction_id}")
    print(f"初始状态: {txn.state}")
    print()

    # Advance through governance chain
    print("开始推进治理链...")
    print("-" * 60)
    txn = sm.advance(txn)
    print("-" * 60)

    print(f"\n最终状态: {txn.state}")
    if txn.state == "complete":
        print("治理链执行成功!")
        if txn.integrated_result:
            print(f"\n整合结果:\n{txn.integrated_result[:500]}...")
    elif txn.state == "error":
        print(f"治理链执行失败!")
        errors = [e for e in txn.audit_trail if e.get("action") == "error"]
        if errors:
            print(f"错误: {errors[-1].get('error', 'unknown')}")
    elif txn.state == "rejected":
        print("治理链审核被拒绝")
        if txn.review_notes:
            print(f"原因: {txn.review_notes}")

    print(f"\n审计记录: {len(txn.audit_trail)} 条")
    for entry in txn.audit_trail:
        print(f"  [{entry.get('step')}] {entry.get('action')}")

    print(f"\n事务ID: {txn.transaction_id}")
    print(f"可在 Dashboard 查看: http://localhost:9200/tasks/{txn.transaction_id}")

    return txn


if __name__ == "__main__":
    run()
