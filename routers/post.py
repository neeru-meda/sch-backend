from fastapi import APIRouter, HTTPException, Path, Body, Depends
from pydantic import BaseModel

# Request model for like/save endpoints
class UserIdRequest(BaseModel):
    user_id: str
from typing import List
from models import Post
from database import db
from bson import ObjectId
from routers.auth import get_current_user

router = APIRouter(
    prefix="/posts",
    tags=["posts"]
)

def post_helper(post) -> dict:
    return {
        "id": str(post.get("_id")),
        "title": post.get("title"),
        "content": post.get("content"),
        "category": post.get("category"),
        "link": post.get("link"),
        "attachments": post.get("attachments", []),
        "tags": post.get("tags", []),
        "author": post.get("author"),
        "createdAt": post.get("createdAt"),
        "likes": post.get("likes", []),
        "saves": post.get("saves", []),
        "comments": post.get("comments", []),
        # commentsCount will be added dynamically in list_posts
    }

@router.get("/", response_model=List[Post])
async def list_posts():
    posts_cursor = db["posts"].find()
    posts = []
    # Collect all post ids
    post_list = []
    async for post in posts_cursor:
        post_list.append(post)
    post_ids = [str(post["_id"]) for post in post_list]

    print(f"Found {len(post_ids)} posts: {post_ids}")

    # Get comment counts for all posts in one query
    comment_counts = {}
    comments_cursor = db["comments"].aggregate([
        {"$match": {"post_id": {"$in": post_ids}}},
        {"$group": {"_id": "$post_id", "count": {"$sum": 1}}}
    ])
    async for c in comments_cursor:
        comment_counts[c["_id"]] = c["count"]
    
    print(f"Comment counts: {comment_counts}")

    for post in post_list:
        post_dict = post_helper(post)
        post_id = str(post["_id"])
        post_dict["commentsCount"] = comment_counts.get(post_id, 0)
        posts.append(post_dict)
    return posts

@router.post("/", response_model=Post)
async def create_post(post: Post, current_user=Depends(get_current_user)):
    post_dict = post.dict(exclude_unset=True)
    result = await db["posts"].insert_one(post_dict)
    post_dict["id"] = str(result.inserted_id)
    return post_dict

@router.get("/{post_id}", response_model=Post)
async def get_post(post_id: str = Path(..., description="The ID of the post to retrieve")):
    post = await db["posts"].find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Get comment count for this post
    comment_count = await db["comments"].count_documents({"post_id": post_id})
    
    post_dict = post_helper(post)
    post_dict["commentsCount"] = comment_count
    return post_dict

@router.put("/{post_id}", response_model=Post)
async def update_post(post_id: str, post: Post, current_user=Depends(get_current_user)):
    existing_post = await db["posts"].find_one({"_id": ObjectId(post_id)})
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")
    if existing_post.get("author", {}).get("_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to update this post")
    post_dict = post.dict(exclude_unset=True)
    result = await db["posts"].update_one({"_id": ObjectId(post_id)}, {"$set": post_dict})
    updated_post = await db["posts"].find_one({"_id": ObjectId(post_id)})
    return post_helper(updated_post)

@router.delete("/{post_id}")
async def delete_post(post_id: str, current_user=Depends(get_current_user)):
    existing_post = await db["posts"].find_one({"_id": ObjectId(post_id)})
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")
    if existing_post.get("author", {}).get("_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this post")
    result = await db["posts"].delete_one({"_id": ObjectId(post_id)})
    return {"message": "Post deleted"}

@router.post("/{post_id}/like")
async def like_post(post_id: str, req: UserIdRequest, current_user=Depends(get_current_user)):
    post = await db["posts"].find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    likes = post.get("likes", [])
    user_id = req.user_id
    if user_id in likes:
        likes.remove(user_id)
    else:
        likes.append(user_id)
    await db["posts"].update_one({"_id": ObjectId(post_id)}, {"$set": {"likes": likes}})
    return {"likes": likes}

@router.post("/{post_id}/save")
async def save_post(post_id: str, req: UserIdRequest, current_user=Depends(get_current_user)):
    print(f"Save request - post_id: {post_id}, user_id: {req.user_id}, current_user: {current_user.id}")
    post = await db["posts"].find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    saves = post.get("saves", [])
    user_id = req.user_id
    print(f"Current saves: {saves}, user_id: {user_id}")
    if user_id in saves:
        saves.remove(user_id)
        print(f"Removed user from saves: {saves}")
    else:
        saves.append(user_id)
        print(f"Added user to saves: {saves}")
    await db["posts"].update_one({"_id": ObjectId(post_id)}, {"$set": {"saves": saves}})
    return {"saves": saves}