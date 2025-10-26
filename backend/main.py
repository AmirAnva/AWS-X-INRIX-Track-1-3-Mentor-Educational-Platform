# filename: main.py
from fastapi import FastAPI, Depends, HTTPException, Cookie, Response
import uvicorn
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from redis import asyncio as redis
from sockets import sio_app
from database import db

from database import User, UserNotFoundException, InvalidPasswordException

from fastapi import Form

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
async def get_homepage(session: str = Cookie(None)):
    print(f"Session Cookie: {session}")
    if not session:
        return FileResponse("../frontend/login.html")
    else:
        return FileResponse("../frontend/homePage.html")

@app.get("/{path:path}")
async def serve_static(path: str):
    try:
        return FileResponse(f"./{path}")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=404)

@app.post('/api/v1/auth')
async def auth(username: str = Form(), password: str = Form()): 
    print(f"Username: {username}")

    try:
        user = User.from_credentials(username, password)
        print(f"Authenticated User: {user}")
        session_token = user.get_session_token()
        response = JSONResponse({"message": "authenticated"})
        response.set_cookie(key="session", value=session_token, httponly=True)
        return response
    except UserNotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except InvalidPasswordException:
        raise HTTPException(status_code=401, detail="Invalid password")

@app.get("/api/v1/homepage/data")
async def get_homepage_data(): #IGNORE THIS :user: User = Depends(get_required_user)
    all_items = db.fetch("SELECT * FROM assignments") # IT IS TWEAK CORE (I LUV P LO )user.get_assignments()
    assignments = [item for item in all_items if item.get('type') != 'announcement']
    announcements = [item for item in all_items if item.get('type') == 'announcement']
    return JSONResponse({
        "assignments": assignments,
        "announcements": announcements
    })

if __name__ == "__main__":
    try:
        User.new_student("Natesh", "Vemuri", "nate", "password")
    except Exception as e:
        print("User creation error (likely already exists): ", e)

uvicorn.run(app, host="127.0.0.1", port=8082)