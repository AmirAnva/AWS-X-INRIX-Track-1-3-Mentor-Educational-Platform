# filename: main.py
from eventlet import patcher, GreenPool
patcher.monkey_patch(all=True)

from fastapi import FastAPI, Depends, HTTPException, Cookie, Response
import uvicorn
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from redis import asyncio as redis
from sockets import sio_app
from database import db

from database import User, UserNotFoundException, InvalidPasswordException, Assignment

from fastapi import Form
from fastapi import File, UploadFile
from io import BytesIO
import subprocess
import requests

from aws import upload_file_to_s3, delete_file_from_s3, transcribe_file_from_s3, wait_for_transcription_job, find_submission_errors

app = FastAPI()
app.mount('/socket.io', sio_app)
pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    decode_responses=True,
    db=0
)

redis_client = redis.Redis(connection_pool=pool)
    
@app.get("/")
async def get_homepage(session: str = Cookie(None)):
    print(f"Session Cookie: {session}")
    if not session:
        return FileResponse("../frontend/login.html")
    else:
        return FileResponse("../frontend/homePage.html")

@app.post("/api/v1/submit")
async def submit():
    pass

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

@app.post('/api/v1/pair_user')
async def pair_user(response: Response, session: str = Cookie(None), pairingCode: str = Form()):
    user = User.from_session(session)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    print(user)
    if not user.is_mentor:
        raise HTTPException(status_code=403, detail="Only mentors can pair with students")

    try: 
        pairingCode = int(pairingCode)
    except ValueError:
        return JSONResponse({"error": "Invalid student ID"}, status_code=400)
    
    student = User.from_id(int(pairingCode))
    if not student:
        return JSONResponse({"error": "Student not found"}, status_code=404)

    if student.is_mentor:
        return JSONResponse({"error": "Cannot pair with another mentor"}, status_code=400)
    
    try:
        User.pair_users(mentor_id=user.id, student_id=student.id)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    
    return JSONResponse({"status": "success"})

@app.get('/api/v1/sign_out')
async def sign_out(session: str = Cookie(None)):
    user = User.from_session(session)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    user.clear_sessions()
    response = JSONResponse({"message": "signed out"})
    response.delete_cookie(key="session")
    return response

@app.get("/api/v1/home")
async def get_homepage_data(session: str = Cookie(None)):
    user = User.from_session(session)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    assignments = user.get_assignments()
    assignments = [a.to_json() for a in assignments]
    return {"first_name": user.first_name, "last_name": user.last_name, "username": user.username, "user_type": user.is_mentor, "is_paired": user.paired_id, "assignments": assignments}


TEMP_MOVIE_FOLDER = "./temp/movies/"
import os
os.makedirs(TEMP_MOVIE_FOLDER, exist_ok=True)

@app.post('/api/v1/create_assignment')
async def create_assignment(session: str = Cookie(None), title: str = Form(), description: str = Form(), due_date: str = Form(), file: UploadFile = File(None)):
    user = User.from_session(session)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    if not user.is_mentor:
        raise HTTPException(status_code=403, detail="Only mentors can create assignments")
    
    print(f"Creating assignment with title: {title}, description: {description}, due_date: {due_date}")

    assignment = Assignment.new(user)
    assignment.set_title(title)
    assignment.set_description(description)
    assignment.set_due_date(due_date)

    if file:
        file_content = await file.read()
        file_path = os.path.join(TEMP_MOVIE_FOLDER, f"assignment_{assignment.id}")
        with open(file_path, "wb") as f:
            f.write(file_content)

    return {"status": "success", "assignment_id": assignment.id}

@app.get('/api/v1/assignment_file/{assignment_id}')
async def get_assignment_file(assignment_id: int, session: str = Cookie(None)):
    user = User.from_session(session)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    assignment = Assignment.from_id(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    file_path = os.path.join(TEMP_MOVIE_FOLDER, f"assignment_{assignment.id}")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Assignment file not found")
    
    return FileResponse(file_path, media_type='application/octet-stream', filename=f"assignment_{assignment.id}")

    import subprocess

@app.post('/api/v1/submit_assignment')
async def submit_assignment(session: str = Cookie(None), assignment_id: int = Form(), content: str = Form()):
    user = User.from_session(session)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    user.submit_assignment(assignment_id, content)

    
    # extract audio from the video
    # transcribe with aws transcribe
    # prompt with amazon bedrock
    # cry :_(
    # sleep

    # STEP 1
    video_path = os.path.join(TEMP_MOVIE_FOLDER, f"assignment_{assignment_id}")
    if not os.path.exists(video_path):
        return {"status": "success"}
    
    audio_path = os.path.join(TEMP_MOVIE_FOLDER, f"assignment_{assignment_id}_audio.wav")
    subprocess.run([
        "ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", audio_path
    ], check=True)

    upload_file_to_s3(audio_path, f"assignment_{assignment_id}_audio")
    transcribe_file_from_s3(f"assignment_{assignment_id}_audio", f"transcription_job_{assignment_id}")
    response = wait_for_transcription_job(f"transcription_job_{assignment_id}")
    delete_file_from_s3(f"assignment_{assignment_id}_audio")

    transcript_url = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
    transcript_response = requests.get(transcript_url)
    transcript_data = transcript_response.json()
    transcript_text = transcript_data['results']['transcripts'][0]['transcript']

    errors = find_submission_errors(transcript_text, content)

    user.add_ai_review_to_submission(assignment_id, errors)
    
    return {"status": "success"}



@app.get("/{path:path}")
async def serve_static(path: str):
    try:
        return FileResponse(f"../frontend/{path}")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=404)


if __name__ == "__main__":
    try:
        
        User.new("Amir", "Anvarkhujaev", "amir", "password", 0);
        User.new("Ben", "castillo", "ben", "password", 1);
    except Exception as e:
        print("User creation error (likely already exists): ", e)


if __name__=="__main__":
    uvicorn.run(app, host="0.0.0.0", port=8082)
