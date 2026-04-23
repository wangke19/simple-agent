import logging

from dotenv import load_dotenv

from simple_agent import SimpleAgent
from simple_agent.tools import CalculatorTool, GitTool, SearchTool

load_dotenv()


def main():
    agent = SimpleAgent()
    agent.register_tool(SearchTool())
    agent.register_tool(CalculatorTool())
    agent.register_tool(GitTool())

    result = agent.run("这个项目最近3条提交记录是什么？")
    print(result)


if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    main()
