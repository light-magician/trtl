from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.tools import ShellTool, WikipediaQueryRun
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_openai import OpenAIEmbeddings

import trtl
from trtl.memory import save_persistent_memory, search_persistent_memories
from trtl.tools.enhanced_terminal import EnhancedTerminal
from trtl.tools.image_gen import OpenAIImageTool

# from shell_enhanced import ShellEnhanced

# internet search
"""
using Tavily for now to facilitate internet searches, only get 1k 
requests per month

this is imported in the 
"""
tavily_web_search = TavilySearchResults(max_results=5)

"""
The shell_commands tool gives the agent access to command line execution 
    when running in the command line. This works well when 
    the user is operating from the command line with admin access,
    but there will be permissions issues when we are running from 
    the app layer, and apple tries to stop us.
"""
terminal = ShellTool()

# Chroma RAG for CLI manuals (TLDR pages)
PROJECT_ROOT = Path(trtl.__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

cli_rag_retriever = Chroma(
    persist_directory=str(DATA_DIR),
    collection_name="tldr_manuals",
    embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
).as_retriever(search_kwargs={"k": 4})

# Enhanced shell tool with CLI tool discovery, retrieval, and execution
enhanced_terminal = EnhancedTerminal(retriever=cli_rag_retriever)

"""
invoke wikipedia search with this tool
"""
wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

image_gen = OpenAIImageTool()
"""
This is the export of this file.
Define tools and put them in here,
    the agent class will import them.

Some memory is implemented as tools, 
    like save_persistent_memory
    and search_persistent_memories.
    Those too will need to be imported here.
"""
tool_belt = [
    save_persistent_memory,
    search_persistent_memories,
    tavily_web_search,
    terminal,
    enhanced_terminal,
    wikipedia,
    image_gen,
]
