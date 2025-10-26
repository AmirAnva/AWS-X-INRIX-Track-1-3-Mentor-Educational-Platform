import socketio
import uvicorn
from fastapi import FastAPI, Request
from http.cookies import SimpleCookie
from database import User, Scratchpad
from diff_match_patch import diff_match_patch

redis_manager = socketio.AsyncRedisManager('redis://localhost:6379')

client_origin = [
    "http://localhost:8082",
    "http://127.0.0.1:8082"
    ]  

sio = socketio.AsyncServer(
    async_mode='asgi',
    client_manager=redis_manager,
    cors_allowed_origins=client_origin #THIS NEEDS TO BE CHANGED OTHERWISE COOKIES WONT WORK IT REQUIRES A SPECIFIC ORIGIN LIST
)

sio_app = socketio.ASGIApp(sio)

@sio.event
async def connect(sid, environ):
    print("Client connected, sid ",sid)
    cookie_header = environ.get('HTTP_COOKIE')
    if not cookie_header:
        print("No auth provided, rejecting")
        return False
    print("PAST COOKIE CHECK")
    cookie = SimpleCookie()
    cookie.load(cookie_header)

    session_id = cookie.get('session').value if cookie.get('session') else None

    if not session_id:
        print("No session_id cookie, rejecting")
        return False
    print("PAST SESSION_ID CHECK")
    user = User.from_session(session_id)
    if not user:
        print("Invalid session, rejecting")
        return False
    print("PAST USER CHECK")
    mentor = user.get_paired_user()
    mentor_id = mentor.id if mentor else None
    print("PAST MENTOR")
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
    if (not scratchpad_id):
        print("No scratchpad_id provided by user. Making new ")
        scratchpad = Scratchpad.create_new(user.pairing_group_id)
        
    current_scratchpad = Scratchpad.from_id(scratchpad_id)
    if not current_scratchpad:
        print("Scratchpad not found for id ", scratchpad_id)
        return
    current_text = current_scratchpad.content
    patches = dmp.patch_fromText(patch_text)
    (new_text, _) = dmp.patch_apply(patches, current_text)
    if all(_):
        current_scratchpad.set_content(new_text)
        await sio.emit('scratchpad_updated', {'status':'ok'}, room=f"user_{user_id}")
    else:
        await sio.emit('scratchpad_desync', {'status':'desync', 'full_content':current_text}, room=f"user_{user_id}")

@sio.event
async def pingpong(sid):
    print("Received ping from sid ", sid)
    session = await sio.get_session(sid)
    user_id = session['user_id']
    user = User.from_id(user_id)
    if not user:
        print("User not found for sid ", sid)
        return
    print("Sending pong to user ", user.username)
    await sio.emit('pong', {'message': 'pong'}, room=sid)
    

@sio.event
async def disconnect(sid):
    print("Client disconnected, sid ",sid)
    