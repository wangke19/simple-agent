"""Create app.py — single step: just write the file."""
import logging

from dotenv import load_dotenv

from simple_agent import SimpleAgent
from simple_agent.tools import WriteTool, BashTool

load_dotenv()

WORK_DIR = "demo/inventory_app"


def main():
    logging.basicConfig(level="INFO")

    agent = SimpleAgent()
    agent._system_prompt = """你是Python GUI专家。你的唯一任务是调用 file_write 工具创建 app.py 文件。
file_write 工具参数说明：
- path: 文件名，例如 "app.py"
- content: 文件的完整代码内容

请直接调用 file_write，不要输出文字。必须一次性写出完整代码。"""

    agent.register_tool(WriteTool(working_dir=WORK_DIR))
    agent.register_tool(BashTool(working_dir=WORK_DIR, timeout=10))

    task = (
        '请用 file_write 创建 app.py。db.py 中有一个 Database 类，'
        '有 add_product/close/connect/delete_product/get_all_products/'
        'get_product/get_purchases/get_sales/purchase_product/sell_product/'
        'update_product 方法。'
        'app.py 使用 tkinter+ttk 创建进销存GUI，4个Notebook标签页'
        '（商品管理、进货登记、销售登记、库存查看），用Treeview显示数据。'
        '写完后运行 python -c "import app" 验证无错。'
    )

    result = agent.run(task, max_steps=4)
    print(f"\n{'='*60}")
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
