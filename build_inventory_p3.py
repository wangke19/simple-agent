"""Create app.py using simple-agent — focused on single file creation."""
import logging

from dotenv import load_dotenv

from simple_agent import SimpleAgent
from simple_agent.tools import (
    BashTool, ReadTool, WriteTool,
)

load_dotenv()

WORK_DIR = "demo/inventory_app"


def main():
    logging.basicConfig(level="INFO")

    agent = SimpleAgent()
    agent._system_prompt = """你是一个Python GUI开发专家。
你只有两个任务：1) 读取 db.py 了解接口  2) 创建 app.py。
file_write 工具参数：path（文件名如 app.py），content（完整代码内容）。
请一次性写出完整的 app.py，不要分多次。"""

    agent.register_tool(ReadTool(working_dir=WORK_DIR))
    agent.register_tool(WriteTool(working_dir=WORK_DIR))
    agent.register_tool(BashTool(working_dir=WORK_DIR, timeout=10))

    task = (
        "第一步：用 file_read 读取 db.py 了解 Database 类的接口。\n"
        "第二步：用 file_write 创建 app.py。\n\n"
        "app.py 是一个 tkinter 进销存GUI，使用 db.py 的 Database 类。\n"
        "要求：\n"
        "- 主窗口标题 '进销存管理系统'\n"
        "- ttk.Notebook 四个标签页：商品管理、进货登记、销售登记、库存查看\n"
        "- 商品管理：Treeview表格 + 增删改按钮\n"
        "- 进货/销售：Combobox选商品 + 数量单价输入 + 保存按钮\n"
        "- 库存查看：Treeview显示商品名和库存\n"
        "- 第三步：运行 python -c 'import app' 验证无语法错误"
    )

    result = agent.run(task, max_steps=6)
    print(f"\n{'='*60}")
    print(f"Agent result: {result}")


if __name__ == "__main__":
    main()
