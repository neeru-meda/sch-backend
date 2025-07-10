from fastapi import APIRouter, HTTPException, Path, Body, Depends
from typing import List
from models import Comment
from database import db
from bson import ObjectId
from routers.auth import get_current_user

router = APIRouter(
    prefix="/comments",
    tags=["comments"]
)

def comment_helper(comment) -> dict:
    return {
        "id": str(comment.get("_id")),
        "content": comment.get("content"),
        "author": comment.get("author"),
        "createdAt": comment.get("createdAt"),
        "likes": comment.get("likes", []),
        "replies": comment.get("replies", []),
        "post_id": str(comment.get("post_id")) if comment.get("post_id") else None,
    }

@router.get("/post/{post_id}", response_model=List[Comment])
async def list_comments(post_id: str):
    print(f"Fetching comments for post_id: {post_id}")
    comments_cursor = db["comments"].find({"post_id": post_id})
    comments = []
    async for comment in comments_cursor:
        comments.append(comment_helper(comment))
    print(f"Found {len(comments)} comments for post_id: {post_id}")
    return comments

@router.get("/user/{user_id}", response_model=List[Comment])
async def list_user_comments(user_id: str):
    print(f"Fetching comments for user_id: {user_id}")
    comments_cursor = db["comments"].find({"author._id": user_id})
    comments = []
    async for comment in comments_cursor:
        comments.append(comment_helper(comment))
    print(f"Found {len(comments)} comments for user_id: {user_id}")
    return comments

@router.post("", response_model=Comment)
async def create_comment(comment: Comment, current_user=Depends(get_current_user)):
    print(f"Received comment data: {comment.dict()}")
    comment_dict = comment.dict(exclude_unset=True)
    print(f"Comment dict after exclude_unset: {comment_dict}")
    # post_id must be present in the body
    if not comment_dict.get("post_id"):
        print(f"post_id missing from comment_dict: {comment_dict}")
        raise HTTPException(status_code=400, detail="post_id is required in the comment body")
    result = await db["comments"].insert_one(comment_dict)
    comment_dict["id"] = str(result.inserted_id)
    return comment_dict

@router.put("/{comment_id}", response_model=Comment)
async def update_comment(comment_id: str, comment: Comment, current_user=Depends(get_current_user)):
    existing_comment = await db["comments"].find_one({"_id": ObjectId(comment_id)})
    if not existing_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if existing_comment.get("author", {}).get("_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to update this comment")
    comment_dict = comment.dict(exclude_unset=True)
    result = await db["comments"].update_one({"_id": ObjectId(comment_id)}, {"$set": comment_dict})
    updated_comment = await db["comments"].find_one({"_id": ObjectId(comment_id)})
    return comment_helper(updated_comment)

@router.delete("/{comment_id}")
async def delete_comment(comment_id: str, current_user=Depends(get_current_user)):
    existing_comment = await db["comments"].find_one({"_id": ObjectId(comment_id)})
    if not existing_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if existing_comment.get("author", {}).get("_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this comment")
    result = await db["comments"].delete_one({"_id": ObjectId(comment_id)})
    return {"message": "Comment deleted"}

@router.post("/{comment_id}/like")
async def like_comment(comment_id: str, user_id: str = Body(...), current_user=Depends(get_current_user)):
    comment = await db["comments"].find_one({"_id": ObjectId(comment_id)})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    likes = comment.get("likes", [])
    if user_id in likes:
        likes.remove(user_id)
    else:
        likes.append(user_id)
    await db["comments"].update_one({"_id": ObjectId(comment_id)}, {"$set": {"likes": likes}})
    return {"likes": likes} 