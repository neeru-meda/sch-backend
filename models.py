from pydantic import BaseModel, EmailStr
from typing import Optional, List

class User(BaseModel):
    id: Optional[str]
    username: str
    email: EmailStr
    password: str

class AuthUser(BaseModel):
    id: Optional[str]
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    bio: Optional[str] = None
    department: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    college: Optional[str] = None
    joined: Optional[str] = None

class CreateUser(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    department: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    college: Optional[str] = None
    joined: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Reply(BaseModel):
    id: Optional[str] = None
    content: str
    author: dict  # { _id: str, name: str }
    createdAt: str
    likes: List[str] = []

class Comment(BaseModel):
    id: Optional[str] = None
    content: str
    author: dict  # { _id: str, name: str }
    createdAt: str
    likes: List[str] = []
    replies: List[Reply] = []
    post_id: str

class Post(BaseModel):
    id: Optional[str] = None
    title: str
    content: str
    category: str
    link: Optional[str] = None
    attachments: List[str] = []
    tags: List[dict] = []  # [{ _id: str, name: str }]
    author: dict
    createdAt: str
    likes: List[str] = []
    saves: List[str] = []
    commentsCount: Optional[int] = 0
    # comments: List[Comment] = []