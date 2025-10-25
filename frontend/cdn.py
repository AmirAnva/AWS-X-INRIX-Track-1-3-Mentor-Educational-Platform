from fastapi import FastAPI
import uvicorn
from fastapi.responses import FileResponse, JSONResponse
app = FastAPI()
@app.get("/homepage")
async def get_homepage():
    try:
        return FileResponse("../frontend/homePage.html")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=404)

@app.get("/{path:path}")
async def serve_static(path: str):
    import os
    print(os.listdir("."))
    try:
        return FileResponse(f"./{path}")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=404)

uvicorn.run(app, host="127.0.0.1", port=8081)