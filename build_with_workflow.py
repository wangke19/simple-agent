"""Build inventory app using DevWorkflow: plan → decompose → execute → report."""
import logging

from dotenv import load_dotenv

from simple_agent import SimpleAgent, DevWorkflow
from simple_agent.tools import (
    BashTool, EditTool, GrepTool, ReadTool, WriteTool,
)

load_dotenv()

WORK_DIR = "demo/inventory_app2"


def main():
    logging.basicConfig(level="INFO")

    agent = SimpleAgent(max_failures=3)
    agent._system_prompt = """你是一个Python开发专家。使用工具创建和修改文件，运行命令。
file_write 工具参数：path（文件名），content（完整代码）。
每次只完成一个明确的任务，完成后给出简要总结。"""

    agent.register_tool(WriteTool(working_dir=WORK_DIR))
    agent.register_tool(ReadTool(working_dir=WORK_DIR))
    agent.register_tool(EditTool(working_dir=WORK_DIR))
    agent.register_tool(GrepTool(working_dir=WORK_DIR))
    agent.register_tool(BashTool(working_dir=WORK_DIR, timeout=30))

    wf = DevWorkflow(agent, report_dir=f"{WORK_DIR}/.reports")

    requirement = (
        "创建一个进销存管理GUI应用程序（tkinter + SQLite）。\n"
        "需要：db.py（数据库层，products/purchases/sales三表CRUD），"
        "app.py（GUI层，4个标签页：商品管理/进货登记/销售登记/库存查看）。"
    )

    # Phase 1: Plan
    print("=" * 60)
    print("Phase 1: Planning")
    print("=" * 60)
    plan = wf.plan_task(requirement)
    print(plan)
    print()

    # Phase 2: Decompose into atomic tasks
    print("=" * 60)
    print("Phase 2: Decomposing")
    print("=" * 60)
    tasks = wf.decompose(requirement)
    for i, t in enumerate(tasks):
        print(f"  [{i+1}] {t}")
    print()

    # Phase 3: Execute each task
    print("=" * 60)
    print("Phase 3: Executing")
    print("=" * 60)
    result = wf.execute(max_steps_per_task=8)
    print()
    print(result)
    print()

    # Print final report location
    if wf.report:
        print(f"Report status: {wf.report.status}")
        print(f"Total steps: {wf.report.total_steps}, Failures: {wf.report.failed_steps}")

    if wf.report.status == "paused":
        print("\n>>> Agent paused. To resume:")
        print(">>> wf.resume('your guidance here')")


if __name__ == "__main__":
    main()
