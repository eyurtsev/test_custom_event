"""Define a simple chatbot agent.

This agent returns a predefined response without using an actual LLM.
"""

import asyncio
import time
import uuid
from datetime import datetime

from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.types import StreamWriter

from agent.state import State


def slow_sync_call():
    time.sleep(0.1)
    return "result"


async def my_node(state: State, config: RunnableConfig, writer: StreamWriter):
    """Each node does work."""
    tic = time.time()
    id_ = str(uuid.uuid4())
    writer("hello")
    await adispatch_custom_event(
        "my_event",
        {
            "idx": 1,
            "status": "starting slow call",
            "tic": tic,
            "id": id_,
            "toc_scheduled": datetime.fromtimestamp(tic).strftime("%M:%S.%f")[:-3],
        },
        config=config,
    )
    # Don't do this! It's blocking the event loop completely killing
    # parallelism in the server!
    slow_sync_call()
    # Correct way to call blocking call
    # await asyncio.to_thread(slow_sync_call)
    toc = time.time()
    await adispatch_custom_event(
        "my_event",
        {
            "idx": 2,
            "status": "finishing slow call",
            "toc": toc,
            "delta_time": toc - tic,
            "id": id_,
            "toc_scheduled": datetime.fromtimestamp(toc).strftime("%M:%S.%f")[:-3],
        },
        config=config,
    )
    return {
        "foo": id_,
    }


# Define a new graph
workflow = StateGraph(State)

# Add the node to the graph
workflow.add_node("my_node", my_node)

# Set the entrypoint as `call_model`
workflow.add_edge("__start__", "my_node")

# Compile the workflow into an executable graph
graph = workflow.compile()
graph.name = "New Graph"  # This defines the custom name in LangSmith
