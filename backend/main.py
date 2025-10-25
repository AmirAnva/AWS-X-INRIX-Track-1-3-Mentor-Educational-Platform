# filename: main.py
from fastapi import FastAPI
import uvicorn
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from redis import asyncio as redis
from sockets import sio_app
from database import db

app = FastAPI()
app.mount('/socket.io', sio_app)
pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    decode_responses=True,
    db=0
)

redis_client = redis.Redis(connection_pool=pool)
    
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>WebSocket Test</title>
    </head>
    <body>
        <h1>FastAPI WebSocket Demo</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id="messages"></ul>
        <script>
            const ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = (event) => {
                const messages = document.getElementById('messages');
                const li = document.createElement('li');
                li.textContent = event.data;
                messages.appendChild(li);
            };
            function sendMessage(event) {
                const input = document.getElementById("messageText");
                ws.send(input.value);
                input.value = '';
                event.preventDefault();
            }
        </script>
    </body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)





@app.get("/homepage")
async def get_homepage():
    try:
        return FileResponse("../frontend/homePage.html")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=404)

@app.get("/homepage/data")
async def get_homepage_data():
    all_items = db.fetch("SELECT * FROM assignments")
    assignments = [item for item in all_items if item.get('type') != 'announcement']
    announcements = [item for item in all_items if item.get('type') == 'announcement']
    return JSONResponse({
        "assignments": assignments,
        "announcements": announcements
    })





uvicorn.run(app, host="127.0.0.1", port=8082)