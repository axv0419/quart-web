import asyncio
import datetime
import os
from typing import Optional
from quart import jsonify, make_response, Quart, render_template, request

app = Quart(__name__)
app.clients = set()

class ServerSentEvent:

    def __init__(
            self,
            data: str,
            *,
            event: Optional[str]=None,
            id: Optional[int]=None,
            retry: Optional[int]=None,
    ) -> None:
        self.data = data
        self.event = event
        self.id = id
        self.retry = retry

    def encode(self) -> bytes:
        message = f"data: {self.data}"
        if self.event is not None:
            message = f"{message}\nevent: {self.event}"
        if self.id is not None:
            message = f"{message}\nid: {self.id}"
        if self.retry is not None:
            message = f"{message}\nretry: {self.retry}"
        message = f"{message}\r\n\r\n"
        return message.encode('utf-8')



@app.route('/', methods=['GET'])
async def index():
    if 'html' in request.headers.get('Accept',''):
        return await render_template('index.html')
    return jsonify(dict(status="ok",timestamp=datetime.datetime.now(),server=os.environ.get('HOSTNAME')))

@app.route('/health', methods=['GET'])
async def health():
    return jsonify(dict(status='up'))


@app.route('/', methods=['POST'])
async def broadcast():
    data = await request.get_json()
    for queue in app.clients:
        await queue.put(data['message'])
    return jsonify(True)

@app.route('/sse')
async def sse():
    queue = asyncio.Queue()
    app.clients.add(queue)
    async def send_events():
        while True:
            await asyncio.sleep(4)
            try:
                data = await queue.get()
                event = ServerSentEvent(data,event="update")
                yield event.encode()
            except asyncio.CancelledError as error:
                app.clients.remove(queue)

    response = await make_response(
        send_events(),
        {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            # 'Transfer-Encoding': 'chunked',
        },
    )
    await queue.put("OK")
    response.timeout = None
    return response

if __name__ == "__main__":
    app.run()
