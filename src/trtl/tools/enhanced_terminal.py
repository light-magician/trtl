import subprocess
from typing import Optional, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

"""
Tool class that allows agent to search for famous command line tools
stored in a Chroma RAG DB.

TODO: 
If retriever changes often, or you plan to have tools that hot-swap
underlying behavior (e.g. different RAGs), then using 
Tool.from_function with closures is much cleaner and more maintainable.
"""


class EnhancedTerminalInput(BaseModel):
    tool_name: str = Field(..., description="The CLI tool to use, like 'convert'")
    task_description: str = Field(
        ..., description="What to do, e.g., 'resize image to 50%'"
    )
    inputs: Optional[str] = Field(None, description="Optional input args or filenames")


class EnhancedTerminal(BaseTool):
    name: str = "enhanced_terminal"
    description: str = (
        "This tool is a major upgrade to the terminal. It equips trtl with a knowledge base on the most popular "
        "command line tools, and how and when to use them. It allows trtl to download the tools if it does not "
        "yet have access to them, verify their installation, verify their output when used, and use them in succession."
        "trtl will use this tool when it needs to perform OS level or File System actions and it is unsure how. "
        "trtl will craft its own natural langauge query to try to find the best tool or host of tools that it may need to "
        "accomplish a user specified task. It will use this tool in succession if more than one tool is needed, or more than "
        "one tool action is necessary."
        "Some example tools include, cat, grep, ffmpeg, imagemagick, convert"
        "This tool searches a database of CLI usage examples (like TLDR pages) to find commands relevant to your task. "
        "It checks if the required CLI tool is installed (like 'convert' or 'ffmpeg'), installs it via Homebrew if missing, "
        "and executes the resulting command. You may craft your own natural language query to help retrieve the correct CLI syntax."
    )
    args_schema: Type[BaseModel] = EnhancedTerminalInput
    _retriever: any = PrivateAttr()

    def __init__(self, retriever, **kwargs):
        super().__init__(**kwargs)
        self._retriever = retriever

    def _run(
        self, tool_name: str, task_description: str, inputs: Optional[str] = None
    ) -> str:
        if not self.check_tool_installed(tool_name):
            install_result = self.install_tool(tool_name)
            if "Error" in install_result:
                return install_result

        command = self.search_command_example(task_description, tool_name)
        if not command:
            return f"Could not find a relevant command for {tool_name} and task '{task_description}'."

        return self.run_command(command)

    def check_tool_installed(self, tool_name: str) -> bool:
        return (
            subprocess.call(
                f"which {tool_name}",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            == 0
        )

    def install_tool(self, tool_name: str) -> str:
        """
        install the command line tool if we need it
        """
        try:
            result = subprocess.run(
                f"brew install {tool_name}",
                shell=True,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout or "Tool installed."
        except subprocess.CalledProcessError as e:
            return f"Error installing {tool_name}: {e.stderr}"

    def search_command_example(
        self, task_description: str, tool_name: str
    ) -> Optional[str]:
        """
        search out examples of the CLI usage
        """
        query = f"{task_description} using {tool_name}"
        docs = self._retriever.get_relevant_documents(query)
        for doc in docs:
            lines = doc.page_content.splitlines()
            for line in lines:
                if tool_name in line and line.strip().startswith("`"):
                    return line.strip("` ")
        return None

    def run_command(self, command: str) -> str:
        """
        run the program

        TODO: it is possible that we should be just crafting the command
              with this tool class and letting the Shell Tool execute.
        """
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout or "Command executed successfully."
            else:
                return f"Command failed with error: {result.stderr}"
        except Exception as e:
            return f"Execution error: {str(e)}"
