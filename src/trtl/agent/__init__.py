# system prompt
import os
import sqlite3
from pathlib import Path
from typing import Iterator, List

import tiktoken
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from trtl.memory import persistent_memory_vector_store
from trtl.tools import tool_belt


# ============================================================================
# Graph + Agent Class
# ============================================================================
class State(MessagesState):
    recall_memories: List[str]


# the system prompt
with open("src/trtl/config/system_prompt.txt") as f:
    system_prompt = f.read()

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("placeholder", "{messages}"),
    ]
)


class Agent:
    def __init__(self):
        self.model = ChatOpenAI(model_name="gpt-4o")
        self.tokenizer = tiktoken.encoding_for_model("gpt-4o")
        self.tools = tool_belt
        self.model_with_tools = self.model.bind_tools(self.tools)
        # persistent memory is ALWAYS accessible to the agent
        self.persistent_memory = persistent_memory_vector_store.as_retriever()
        # TODO: swap this to a SQLite memory saver later
        self.chat_history = MemorySaver()
        """TODO:
        chat config maintains info about the current user via user_id 
            and chat history via thread_id 
        if we swap user or thread the LLM will not reason using past
            experience from whichever user or via whichever permanent
            chat history 
        We have to make the thread_id configuratble later, as people request
            to be able to quickly open a "context-less" chat 
        """
        self.chat_config = {"configurable": {"user_id": "1", "thread_id": "1"}}

        # Setup LangGraph
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(State)

        builder.add_node("load_memories", self._load_memories)
        builder.add_node("agent", self._create_agent)
        builder.add_node("tools", ToolNode(self.tools))

        builder.add_edge(START, "load_memories")
        builder.add_edge("load_memories", "agent")
        builder.add_conditional_edges("agent", self._route_tools, ["tools", END])
        builder.add_edge("tools", "agent")

        return builder.compile(checkpointer=self.chat_history)

    def _load_memories(self, state: State) -> State:
        user_messages = [
            m.content for m in state["messages"] if isinstance(m, HumanMessage)
        ]
        query = user_messages[-1] if user_messages else ""

        # Filter by user_id like your tool does
        user_id = self.chat_config["configurable"]["user_id"]
        documents = persistent_memory_vector_store.similarity_search(
            query, k=3, filter={"user_id": user_id}
        )
        recall_memories = [doc.page_content for doc in documents]

        return {**state, "recall_memories": recall_memories}

    def _create_agent(self, state: State) -> State:
        bound = prompt | self.model_with_tools
        recall_str = (
            "<recall_memory>\n"
            + "\n".join(state["recall_memories"])
            + "\n</recall_memory>"
        )
        prediction = bound.invoke(
            {
                "messages": state["messages"],
                "recall_memories": recall_str,
            }
        )
        # Optional: Save this exchange to SQLite history (not surfaced now)
        return {"messages": [prediction]}

    def _route_tools(self, state: State):
        msg = state["messages"][-1]
        return "tools" if getattr(msg, "tool_calls", None) else END

    def request(self, prompt: str) -> Iterator:
        """
        returns an Iterator over a stream of chunks
            so that this can be called by different
            pieces of code that might want to display
            the stream (CLI, native UI)
        """
        return self.graph.stream(
            input={"messages": [HumanMessage(prompt)]},
            config=self.chat_config,
            stream_mode="messages",
        )
