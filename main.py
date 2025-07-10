from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import db
from fastapi import HTTPException
import os

app = FastAPI()

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

# CORS settings for frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Backend is running!"}

@app.get("/db-test")
async def db_test():
    try:
        collections = await db.list_collection_names()
        return {"collections": collections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Routers will be included here
from routers import user
app.include_router(user.router)
from routers import post
app.include_router(post.router)
from routers import comment
app.include_router(comment.router)
from routers import auth
app.include_router(auth.router)
