from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, status, Depends
from app.core.supabase_client import get_supabase_client
from app.api.routes.auth import get_current_user, UserResponse

router = APIRouter(prefix="/user", tags=["user"])


class UserProfile(BaseModel):
    name: str
    email: str
    role: str = ""
    bio: str = ""


class UserProfileResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    bio: str = ""


@router.get("/profile", response_model=UserProfileResponse)
def get_profile(current_user: UserResponse = Depends(get_current_user)):
    try:
        client = get_supabase_client()
        res = client.table("users").select("*").eq("id", current_user.id).single().execute()

        if not res.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        data = res.data
        return UserProfileResponse(
            id=data.get("id", ""),
            name=data.get("name", ""),
            email=data.get("email", ""),
            role=data.get("role", ""),
            bio=data.get("bio", ""),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch user profile") from exc


@router.put("/profile", response_model=UserProfileResponse)
def update_profile(profile: UserProfile, current_user: UserResponse = Depends(get_current_user)):
    try:
        client = get_supabase_client()
        updated = client.table("users").update({
            "name": profile.name,
            "email": profile.email,
            "role": profile.role,
            "bio": profile.bio,
        }).eq("id", current_user.id).execute()

        if not updated.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        data = updated.data[0]
        return UserProfileResponse(
            id=data.get("id", ""),
            name=data.get("name", ""),
            email=data.get("email", ""),
            role=data.get("role", ""),
            bio=data.get("bio", ""),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc