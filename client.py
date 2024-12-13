import asyncio
import time
from datetime import datetime

from langgraph_sdk import get_sync_client

# Langgraph dev
client = get_sync_client(url="http://localhost:2024")
# Langgraph up
# client = get_sync_client(url="http://localhost:8123")


def make_client_call() -> list:
    events = []
    thread = client.threads.create()
    thread_id = thread["thread_id"]

    for chunk in client.runs.stream(
        thread_id,
        "agent",  # Name of assistant. Defined in langgraph.json.
        input={"foo": "bar"},
        stream_mode="events",
    ):
        if chunk.event != "events":
            continue

        if chunk.data["event"] != "on_custom_event":
            continue

        data = chunk.data["data"]
        tic = time.time()
        data["arrived_time"] = datetime.fromtimestamp(tic).strftime("%M:%S.%f")[:-3]
        events.append(data)

    return events


async def main():
    tasks = []
    # Parallelize the client calls
    for _ in range(100):
        tasks.append(asyncio.to_thread(make_client_call))
    results = await asyncio.gather(*tasks)
    print(f'Tested a total of len(results)={len(results)} calls')

    for result in results:
        if result[0]["idx"] != 1:
            raise AssertionError("Missing first event!")
    print("All good")


if __name__ == "__main__":
    asyncio.run(main())
