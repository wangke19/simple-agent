"""Continue building: create app.py for the inventory GUI."""
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
    agent._system_prompt = """你是一个Python开发专家。你可以使用工具来创建文件、读取文件、编辑文件和执行命令。
- 使用 Python 标准库，不引入额外依赖
- 代码要完整可运行，不要省略任何部分
- file_write 工具的参数名是 path 和 content"""

    agent.register_tool(WriteTool(working_dir=WORK_DIR))
    agent.register_tool(ReadTool(working_dir=WORK_DIR))
    agent.register_tool(EditTool(working_dir=WORK_DIR))
    agent.register_tool(BashTool(working_dir=WORK_DIR, timeout=30))

    task = (
        "db.py 已经创建好了。请先用 file_read 读取 db.py 了解数据库层的接口，"
        "然后创建 app.py — 一个使用 tkinter + ttk 的进销存管理GUI。\n\n"
        "app.py 要求：\n"
        "- import db 并调用 db.init_db() 初始化数据库\n"
        "- 使用 ttk.Notebook 实现标签页\n"
        "- 商品管理页：ttk.Treeview 列表 + 添加/删除/修改按钮和对话框\n"
        "- 进货登记页：选择商品、输入数量和单价，保存后自动增加库存\n"
        "- 销售登记页：选择商品、输入数量和单价，保存后自动扣减库存\n"
        "- 库存查看页：Treeview 显示所有商品库存\n"
        "- 界面使用中文\n"
        "- 写完后运行 python app.py 检查无语法或import错误\n"
        "- file_write 的参数：path（文件路径如 app.py），content（文件内容）"
    )

    result = agent.run(task, max_steps=20)
    print(f"\n{'='*60}")
    print(f"Agent result: {result}")


if __name__ == "__main__":
    main()
