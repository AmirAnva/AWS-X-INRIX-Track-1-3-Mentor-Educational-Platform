import socketio
import uvicorn
from fastapi import FastAPI, Request
from http.cookies import SimpleCookie
from database import User, Scratchpad
from diff_match_patch import diff_match_patch

redis_manager = socketio.AsyncRedisManager('redis://localhost:6379')

client_origin = "http://127.0.0.1:8081"  # Change this to your client's origin

sio = socketio.AsyncServer(
    async_mode='asgi',
    client_manager=redis_manager,
    cors_allowed_origins=[client_origin] #THIS NEEDS TO BE CHANGED OTHERWISE COOKIES WONT WORK IT REQUIRES A SPECIFIC ORIGIN LIST
)

sio_app = socketio.ASGIApp(sio)

@sio.event
async def connect(sid, environ, auth):
    print("Client connected, sid ",sid)
    cookie_header = environ.get('HTTP_COOKIE')
    if not cookie_header:
        print("No auth provided, rejecting")
        return False
    
    cookie = SimpleCookie()
    cookie.load(cookie_header)

    session_id = cookie.get('session_id').value if cookie.get('session_id') else None

    if not session_id:
        print("No session_id cookie, rejecting")
        return False
    
    user = User.from_session(session_id)
    if not user:
        print("Invalid session, rejecting")
        return False
    
    mentor = user.get_paired_user()
    mentor_id = mentor.id if mentor else None

    await sio.save_session(sid, {'user_id': user.id, 'mentor_id': mentor_id})
    sio.enter_room(sid, f"user_{user.id}")
    await sio.emit('connected', {'message': 'Successfully connected to WebSocket server.'}, room=f"user_{user.id}")
    await sio.emit('initial_data', {'messages': user.get_conversation_history()}, room=f"user_{user.id}")
    print(f"User {user.username} connected with sid {sid}")
    

@sio.event
async def send_message(sid, data):
    session = await sio.get_session(sid)
    user_id = session['user_id']
    mentor_id = session['mentor_id']

    user = User.from_id(user_id)
    if not user:
        print("User not found for sid ", sid)
        return

    message = data.get('message')
    if not message:
        print("No message provided by user ", user.username)
        return

    user.send_to_paired(message)

    # Emit to mentor if exists
    if mentor_id:
        await sio.emit('new_message', {'sender': user.username, 'message': message}, room=f"user_{mentor_id}")

@sio.event
async def update_scratchpad(sid, data):
    session = await sio.get_session(sid)
    user_id = session['user_id']

    user = User.from_id(user_id)
    if not user:
        print("User not found for sid ", sid)
        return

    patch_text = data.get('patch_text')
    scratchpad_id = data.get('scratchpad_id')
    if patch_text is None:
        print("No patch_text provided by user ", user.username)
        return
    
    dmp = diff_match_patch()
    current_scratchpad = Scratchpad.from_id(scratchpad_id)
    current_text = current_scratchpad.content
    patches = dmp.patch_fromText(patch_text)
    (new_text, _) = dmp.patch_apply(patches, current_text)
    if all(_):
        current_scratchpad.set_content(new_text)
        await sio.emit('scratchpad_updated', {'status':'ok'}, room=f"user_{user_id}")
    else:
        await sio.emit('scratchpad_desync', {'status':'desync', 'full_content':current_text}, room=f"user_{user_id}")

    

@sio.event
async def disconnect(sid):
    print("Client disconnected, sid ",sid)
    