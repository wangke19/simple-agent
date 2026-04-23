import logging

from dotenv import load_dotenv

from simple_agent import SimpleAgent
from simple_agent.tools import CalculatorTool, SearchTool

load_dotenv()


def main():
    agent = SimpleAgent()
    agent.register_tool(SearchTool())
    agent.register_tool(CalculatorTool())

    result = agent.run("北京今天天气怎么样？")
    print(result)


if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    main()
