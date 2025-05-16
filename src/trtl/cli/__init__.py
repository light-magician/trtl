"""
This file handles the command line interaction with the trtl daemon.
"""

import sys
import time
from enum import Enum
from typing import Any, Dict, List, Optional

from rich import box
from rich.align import Align
from rich.box import Box

# TODO: we should use a stream adapter in the agent, and handle
# receiving that stream here
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text


# innocence theme
class Innocence(Enum):
    BLUE = "#7FA6FC"
    GREEN = "#74D4B9"
    PINK = "#F0D1F0"
    BEIGE = "#F0EBEB"
    RED = "#E98181"
    VIOLET = "#A79BDC"
    GREY = "#BFBDC8"
    BLACK = "#65636D"


def _pretty_print_stream_chunk(chunk):
    for node, updates in chunk.items():
        print(f"Update from node: {node}")
        # this is breaking down the json that
        # is returned into just what is nice to show
        # TODO: this is implementation specific and is thus
        # not ideal, possible that this should be refactored in
        # some way but is for now non-essential
        if "messages" in updates:
            updates["messages"][-1].pretty_print()
        else:
            print(updates)

        print("\n")


def cli_loop(agent):
    """
    This is the actual loop the user experiences on the command line.

    All styling and references to any CLI libraries for styling should
        be here or should start from here.

    This project uses rich console for styling terminal output,
        coloration, drawing boxes, ect.
    """

    console = Console()
    while True:
        try:
            prompt = input("\n> ")
            # TODO: here is where we should put other checks for
            # specific commands the user may find convenient
            if prompt.lower() in ("exit", "quit"):
                break
            """
            agent.request(prompt) will give an Iterator to a stream
            of LLM response tokens.
            we can just 
            """
            # for response_chunk in agent.request(prompt):
            # _pretty_print_stream_chunk(response_chunk)
            stream_into_box(agent, prompt, console)
            # TODO: here is where we should be looking for ctrl + c
        except KeyboardInterrupt:
            """
            this is the "control + c" scenario
                for ending the program.
            """
            console.print()
            console.print("👋 🐢 🌸 thanks for spending time with trtl...")
            sys.exit(1)


"""
What is in the splash, 
it HAS TO let the user know how to feel about the application
is it their friend, is it something serious, what level of care was given by its makers?
Are they craftsmen?

It should let them know the purpose of the app, and the first action to take
"""


# ascii art
trtl_daemon_ascii = r"""
                                                                              
  ,--.           ,--.  ,--.       ,--.                                        
,-'  '-.,--.--.,-'  '-.|  |     ,-|  | ,--,--.,---. ,--,--,--. ,---. ,--,--,  
'-.  .-'|  .--''-.  .-'|  |    ' .-. |' ,-.  | .-. :|        || .-. ||      \ 
  |  |  |  |     |  |  |  |    \ `-' |\ '-'  \   --.|  |  |  |' '-' '|  ||  | 
  `--'  `--'     `--'  `--'     `---'  `--`--'`----'`--`--`--' `---' `--''--' 
                                                                              
    """

# a bit more official looking art
trtl_daemon_tron = r"""
████████╗██████╗ ████████╗██╗         ██████╗  █████╗ ███████╗███╗   ███╗ ██████╗ ███╗   ██╗
╚══██╔══╝██╔══██╗╚══██╔══╝██║         ██╔══██╗██╔══██╗██╔════╝████╗ ████║██╔═══██╗████╗  ██║
   ██║   ██████╔╝   ██║   ██║         ██║  ██║███████║█████╗  ██╔████╔██║██║   ██║██╔██╗ ██║
   ██║   ██╔══██╗   ██║   ██║         ██║  ██║██╔══██║██╔══╝  ██║╚██╔╝██║██║   ██║██║╚██╗██║
   ██║   ██║  ██║   ██║   ███████╗    ██████╔╝██║  ██║███████╗██║ ╚═╝ ██║╚██████╔╝██║ ╚████║
   ╚═╝   ╚═╝  ╚═╝   ╚═╝   ╚══════╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
                                                                                            

"""

# custom box definition for the splash
THICK_BOX = Box(
    "████\n"  # Line 1: top_left, top, top_divider, top_right
    "█  █\n"  # Line 2: head_left, spaces, head_vertical, head_right
    "████\n"  # Line 3: head_row_left, head_row_horizontal, head_row_cross, head_row_right
    "█  █\n"  # Line 4: mid_left, spaces, mid_vertical, mid_right
    "████\n"  # Line 5: row_left, row_horizontal, row_cross, row_right
    "████\n"  # Line 6: foot_row_left, foot_row_horizontal, foot_row_cross, foot_row_right
    "█  █\n"  # Line 7: foot_left, spaces, foot_vertical, foot_right
    "████"  # Line 8: bottom_left, bottom, bottom_divider, bottom_right (no \n on the last one)
)


def print_splash(console: Console):
    # center styling
    centered_art = Align.center(
        trtl_daemon_tron, vertical="middle", style=Innocence.PINK.value
    )

    console.print(
        Panel(
            centered_art,
            box=THICK_BOX,
            border_style=Innocence.GREEN.value,
        )
    )


def user_input(console: Console):
    """
    rich dependency will print the input text, so lets just do
    regular python input for now

    first capture their input, then print it as a dimmed shadow
    of what was entered, so the user knows its passed
    """
    return input("> ")


def shadow_user_input(input: str, console: Console):
    """
    takes the user's input and prints out a shadow of it, showing that
    it is in the past tense'
    """
    console.print(
        Panel(
            Text(input, style=Innocence.GREY.value),
            border_style=Innocence.GREY.value,
            title="👤",
            style=Innocence.GREY.value,
        )
    )


def print_tools(tools, console):
    """
    displays what tools the agent has access to.
    """
    tool_content = ""
    for tool in tools:
        tool_name = (
            f"[bold {Innocence.BLUE.value}]{tool.name}[/bold {Innocence.BLUE.value}]"
        )
        tool_description = f"{tool.description}"
        tool_content += f"{tool_name}\n{tool_description}\n\n"

    panel = Panel(
        tool_content,
        title="Tools 🧰",
        title_align="center",
        box=THICK_BOX,
        border_style=Innocence.PINK.value,
    )

    console.print(panel)


class DynamicResponseBox:
    """
    Manages a dynamically growing response box for streaming text from an agent.
    """

    def __init__(self, console: Console):
        self.console = console
        self.live = None
        self.response_text = ""
        self.running = False
        # TODO: define singular panel here

    def start(self, initial_message: str = "Waiting for response..."):
        self.response_text = initial_message

        # Create an initial panel with minimal content
        initial_panel = Panel(
            Markdown(self.response_text),
            border_style=Innocence.BLUE.value,
            # Start with a reasonable width - adjust as needed
            width=40,
        )

        # Start the live display
        self.live = Live(
            initial_panel, console=self.console, refresh_per_second=10, transient=False
        )
        self.live.start()
        self.running = True

    def update(self, text: str):
        if not self.running:
            return

        # Update the response text
        self.response_text = text

        # Create a new panel with updated content
        panel = Panel(
            Markdown(self.response_text),
            border_style=Innocence.BLUE.value,
            # Let the width grow based on content
            width=None,
        )

        # Update the live display
        self.live.update(panel)

    def finish(self):
        if not self.running:
            return

        # Final update with completed content
        final_panel = Panel(
            Markdown(self.response_text),
            border_style=Innocence.BLUE.value,
        )

        # Ensure final update is visible and stop the live display
        if self.live:
            self.live.update(final_panel)
            self.live.stop()
        self.running = False


def stream_into_box(agent, prompt: str, console: Console):
    box = DynamicResponseBox(console)
    box.start()

    try:
        for chunk, metadata in agent.request(prompt):
            # Filter only LLM node outputs if needed
            if "langgraph_node" in metadata:
                # You can optionally filter by node name if your graph has multiple streaming LLMs:
                # if metadata["langgraph_node"] != "llm_response":
                #     continue

                content = getattr(chunk, "content", None)
                if content:
                    box.update(box.response_text + content)
    except Exception as e:
        box.update(f"[red]Error during stream:[/red] {e}")
    finally:
        box.finish()
