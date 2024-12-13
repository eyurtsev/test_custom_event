"""Define a simple chatbot agent.

This agent returns a predefined response without using an actual LLM.
"""

import uuid
from datetime import datetime

import asyncio
import time

from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph

from agent.state import State


def slow_sync_call():
    time.sleep(5)
    return "result"


# Non blocking call


async def my_node(state: State, config: RunnableConfig):
    """Each node does work."""
    tic = time.time()
    id_ = str(uuid.uuid4())
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
    slow_sync_call()
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
