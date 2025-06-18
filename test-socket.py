import asyncio
import websockets

async def test_ws(file_id):
    uri = f"ws://localhost:8000/ws/stream/{file_id}"
    async with websockets.connect(uri, max_size=1024 * 1024 * 10) as websocket:
        try:
            while True:
                msg = await websocket.recv()
                print("Received:", msg)
        except websockets.ConnectionClosed as e:
            print("WebSocket closed by server or lost connection")
            print(e)

asyncio.run(test_ws("stored_demo"))
