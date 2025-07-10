from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import db
from fastapi import HTTPException
import os

app = FastAPI()

# Get allowed origins from environment or use defaults
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []

# Default origins if none specified
default_origins = [
    "http://localhost:3000",
    "http://localhost:5173", 
    "https://neerajaco.netlify.app",
    "https://*.netlify.app",
    "https://*.onrender.com"
]

# Combine environment origins with defaults
allowed_origins = ALLOWED_ORIGINS + default_origins if ALLOWED_ORIGINS else default_origins

# CORS settings for frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Backend is running!", "cors_origins": allowed_origins}

@app.get("/db-test")
async def db_test():
    try:
        collections = await db.list_collection_names()
        return {"collections": collections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cors-test")
def cors_test():
    return {"message": "CORS is working!", "origin": "https://neerajaco.netlify.app"}

# Routers will be included here
from routers import user
app.include_router(user.router)
from routers import post
app.include_router(post.router)
from routers import comment
app.include_router(comment.router)
from routers import auth
app.include_router(auth.router)
