from dotenv import load_dotenv

load_dotenv()

from cli import cli_loop, print_splash, print_tools
from rich.console import Console

from agent import Agent


def main():
    console = Console()
    trtl_agent = Agent()
    print_splash(console)
    print_tools(trtl_agent.tools, console)
    cli_loop(trtl_agent)


if __name__ == "__main__":
    main()
