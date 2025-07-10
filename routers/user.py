from fastapi import APIRouter, HTTPException, Path
from typing import List
from models import User, CreateUser, AuthUser
from database import db
from bson import ObjectId
from routers.auth import get_password_hash

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

def user_helper(user) -> dict:
    return {
        "id": str(user.get("_id")),
        "username": user.get("username"),
        "email": user.get("email"),
    }

@router.get("/", response_model=List[User])
async def list_users():
    users_cursor = db["users"].find()
    users = []
    async for user in users_cursor:
        users.append(user_helper(user))
    return users

@router.post("/", response_model=AuthUser)
async def create_user(user: CreateUser):
    # Check for duplicate username/email
    if await db["users"].find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already registered")
    if await db["users"].find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    user_dict = user.dict()
    user_dict["password"] = get_password_hash(user.password)
    result = await db["users"].insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)
    return AuthUser(
        id=user_dict["id"],
        username=user_dict["username"],
        email=user_dict["email"]
    )

@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str = Path(..., description="The ID of the user to retrieve")):
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_helper(user)

@router.put("/{user_id}", response_model=User)
async def update_user(user_id: str, user: User):
    user_dict = user.dict(exclude_unset=True)
    result = await db["users"].update_one({"_id": ObjectId(user_id)}, {"$set": user_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    updated_user = await db["users"].find_one({"_id": ObjectId(user_id)})
    return user_helper(updated_user)

@router.delete("/{user_id}")
async def delete_user(user_id: str):
    result = await db["users"].delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"} 