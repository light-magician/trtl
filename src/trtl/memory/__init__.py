import uuid
from pathlib import Path
from typing import List

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings

import trtl

# ─── Determine Project Base Directory ──────────────────────────────────────────
# If this file lives at project_root/src/trtl/memory.py, then:
PROJECT_ROOT = Path(trtl.__file__).resolve().parent
PERSIST_DIR = PROJECT_ROOT / "trtl_persisted_memories_db"
PERSIST_DIR.mkdir(parents=True, exist_ok=True)


"""
Going with Chroma DB for the alpha.
Chroma DB is like sqlite for vectors.
Only 15MB for the code and 10's of MB 
    when running idle

The parquet file is automatically created when this 
    at runtime, so no setup is required.

Chroma stores vectors as DuckDB parquet filesl under
    the hood.

It will be reused on the next program run.

TODO: there is a better design for this than instantiating
      right here and giving the tools this access to a 
      randomly declared instance of the vector store.
      Vector store should likely be created as part of Agent
      and should be passed into memory tool...?
"""
persistent_memory_vector_store = Chroma(
    collection_name="trtl_persisted_memories",
    embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
    persist_directory=str(PERSIST_DIR),  # now absolute to project base
)

memory_retriever = persistent_memory_vector_store.as_retriever(search_kwargs={"k": 3})


def _get_user_id(config: RunnableConfig) -> str:
    """
    memories get saved and associated with user ids in
    langgraph so we allow for that here
    """
    user_id = config["configurable"].get("user_id")
    if user_id is None:
        raise ValueError("User ID is required to save/search memory.")
    return user_id


@tool
def save_persistent_memory(memory: str, config: RunnableConfig) -> str:
    """
    This is tool is used for persisting memory accross sessions.
    It can be requested any time by telling trtl to persist whatever info
    is stipulated. trtl will automatically try to save any info about the user
    it thinks will enhance its interactions with them in the future including
    notes on the users file system, habits, personal info, preferences, interests, ect.
    """
    user_id = _get_user_id(config)
    document = Document(
        page_content=memory,
        metadata={"user_id": user_id},
    )
    persistent_memory_vector_store.add_documents([document])
    return memory


@tool
def search_persistent_memories(query: str, config: RunnableConfig) -> List[str]:
    """
    This tool is for searching through persistent memories. trtl can use this whenever
    the user asks about what persistent memories it has access to. trtl will use this
    tool basically all the time to enhance its output and tailor it to the user's
    habits and preferences.
    """
    user_id = _get_user_id(config)

    documents = persistent_memory_vector_store.similarity_search(
        query, k=3, filter={"user_id": user_id}
    )
    return [doc.page_content for doc in documents]
