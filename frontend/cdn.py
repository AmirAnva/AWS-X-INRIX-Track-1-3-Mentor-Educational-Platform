from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
app = FastAPI()
@app.get("/homepage")
async def get_homepage():
    try:
        return FileResponse("../frontend/homePage.html")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=404)
