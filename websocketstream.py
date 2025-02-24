import queue
from typing import Optional

class WebSocketStream:
    """Opens a WebSocket stream as an iterator yielding audio chunks."""

    def __init__(self, websocket, chunk_size: int = 1024):
        self._websocket = websocket
        self._chunk_size = chunk_size
        self._buff = queue.Queue()  # Thread-safe buffer for audio chunks
        self.closed = False

    async def __aenter__(self):
        """Start the WebSocket stream and return the iterator."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the stream and clean up."""
        self.close()

    def close(self):
        """Mark the stream as closed and signal the iterator to stop."""
        self.closed = True
        self._buff.put(None)  # Signal the end of the stream

    async def receive_chunks(self):
        """Continuously receive audio chunks from the WebSocket and add them to the buffer."""
        try:
            while not self.closed:
                data = await self._websocket.receive_bytes()
                self._buff.put(data)
        except Exception as e:
            print(f"WebSocket receive error: {e}")
            self.close()

    def __aiter__(self):
        """Return the iterator object."""
        return self

    async def __anext__(self) -> bytes:
        """Yield the next audio chunk from the buffer."""
        if self.closed:
            raise StopAsyncIteration

        chunk = self._buff.get()
        if chunk is None:
            raise StopAsyncIteration

        data = [chunk]
        while True:
            try:
                chunk = self._buff.get_nowait()
                if chunk is None:
                    raise StopAsyncIteration
                data.append(chunk)
            except queue.Empty:
                break

        return b"".join(data)