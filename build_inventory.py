"""Use simple-agent to build a purchase-sales-inventory GUI application."""
import logging

from dotenv import load_dotenv

from simple_agent import SimpleAgent
from simple_agent.tools import (
    BashTool, EditTool, GrepTool, ReadTool, WriteTool,
)

load_dotenv()

WORK_DIR = "demo/inventory_app"


def main():
    logging.basicConfig(level="INFO")

    agent = SimpleAgent()
    agent._system_prompt = """你是一个Python开发专家。你可以使用工具来创建文件、读取文件、编辑文件、搜索代码和执行命令。

编写代码时请注意：
- 使用 Python 标准库，不引入额外依赖
- 代码要完整可运行，不要省略任何部分
- 每次创建文件时，确保内容完整"""

    # Register development tools pointed at the demo directory
    agent.register_tool(WriteTool(working_dir=WORK_DIR))
    agent.register_tool(ReadTool(working_dir=WORK_DIR))
    agent.register_tool(EditTool(working_dir=WORK_DIR))
    agent.register_tool(GrepTool(working_dir=WORK_DIR))
    agent.register_tool(BashTool(working_dir=WORK_DIR, timeout=30))

    task = (
        "请创建一个进销存管理GUI应用程序，包含以下文件：\n\n"
        "1. db.py - 数据库层，使用 SQLite：\n"
        "   - 创建 products 表（id, name, category, unit, price, stock）\n"
        "   - 创建 purchases 表（id, product_id, quantity, unit_price, total, date）\n"
        "   - 创建 sales 表（id, product_id, quantity, unit_price, total, date）\n"
        "   - 提供完整的增删改查函数\n\n"
        "2. app.py - GUI层，使用 tkinter + ttk：\n"
        "   - 使用 Notebook 实现标签页切换\n"
        "   - 商品管理页：Treeview 列表 + 增删改按钮\n"
        "   - 进货登记页：选择商品、输入数量和单价，自动计算总价并更新库存\n"
        "   - 销售登记页：选择商品、输入数量和单价，自动计算总价并扣减库存\n"
        "   - 库存查看页：显示所有商品当前库存，支持按名称搜索\n"
        "   - 界面全部使用中文\n\n"
        "请先用 file_write 创建 db.py，然后创建 app.py。"
    )

    result = agent.run(task, max_steps=15)
    print(f"\n{'='*60}")
    print(f"Agent result: {result}")


if __name__ == "__main__":
    main()
