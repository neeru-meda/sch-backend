from fastapi import APIRouter, HTTPException, Depends, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from models import User, AuthUser, CreateUser
from database import db
from bson import ObjectId
import os

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise credentials_exception
    return AuthUser(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name"),
        bio=user.get("bio"),
        department=user.get("department"),
        linkedin=user.get("linkedin"),
        github=user.get("github"),
        college=user.get("college"),
        joined=user.get("joined")
    )

@router.post("/register", response_model=AuthUser)
async def register(user: CreateUser):
    if await db["users"].find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already registered")
    if await db["users"].find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    from datetime import datetime, timedelta, timezone
    user_dict = user.dict()
    user_dict["password"] = get_password_hash(user.password)
    # Set joined date to IST if not provided
    if not user_dict.get("joined"):
        ist = timezone(timedelta(hours=5, minutes=30))
        user_dict["joined"] = datetime.now(ist).isoformat()
    result = await db["users"].insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)
    return AuthUser(
        id=user_dict["id"],
        username=user_dict["username"],
        email=user_dict["email"],
        full_name=user_dict.get("full_name"),
        bio=user_dict.get("bio"),
        department=user_dict.get("department"),
        linkedin=user_dict.get("linkedin"),
        github=user_dict.get("github"),
        college=user_dict.get("college"),
        joined=user_dict.get("joined")
    )

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db["users"].find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": str(user["_id"])})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=AuthUser)
async def read_users_me(current_user: AuthUser = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=AuthUser)
async def update_profile(
    full_name: str = Body(None),
    email: str = Body(None),
    bio: str = Body(None),
    department: str = Body(None),
    linkedin: str = Body(None),
    github: str = Body(None),
    college: str = Body(None),
    joined: str = Body(None),
    current_user: AuthUser = Depends(get_current_user)
):
    update_data = {}
    if full_name is not None:
        update_data["full_name"] = full_name
    if email is not None:
        # Check for unique email
        if await db["users"].find_one({"email": email, "_id": {"$ne": ObjectId(current_user.id)}}):
            raise HTTPException(status_code=400, detail="Email already registered")
        update_data["email"] = email
    if bio is not None:
        update_data["bio"] = bio
    if department is not None:
        update_data["department"] = department
    if linkedin is not None:
        update_data["linkedin"] = linkedin
    if github is not None:
        update_data["github"] = github
    if college is not None:
        update_data["college"] = college
    if joined is not None:
        update_data["joined"] = joined
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    await db["users"].update_one({"_id": ObjectId(current_user.id)}, {"$set": update_data})
    user = await db["users"].find_one({"_id": ObjectId(current_user.id)})
    return AuthUser(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name"),
        bio=user.get("bio"),
        department=user.get("department"),
        linkedin=user.get("linkedin"),
        github=user.get("github"),
        college=user.get("college"),
        joined=user.get("joined")
    )

@router.post("/change-password")
async def change_password(old_password: str = Body(...), new_password: str = Body(...), current_user: AuthUser = Depends(get_current_user)):
    user = await db["users"].find_one({"_id": ObjectId(current_user.id)})
    if not user or not verify_password(old_password, user["password"]):
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    hashed = get_password_hash(new_password)
    await db["users"].update_one({"_id": ObjectId(current_user.id)}, {"$set": {"password": hashed}})
    return {"message": "Password changed successfully"} 