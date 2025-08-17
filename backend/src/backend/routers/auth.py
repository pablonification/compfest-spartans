from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

from ..core.config import get_settings
from ..models.user import User
from ..db.mongo import get_database
from ..schemas.auth import GoogleAuthResponse, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

settings = get_settings()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/google/login")
async def google_login():
    """Redirect user to Google OAuth2 consent screen"""
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={settings.GOOGLE_REDIRECT_URI}&"
        "response_type=code&"
        "scope=openid email profile&"
        "access_type=offline"
    )
    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback")
async def google_callback(code: str):
    """Handle Google OAuth2 callback and exchange code for tokens"""
    try:
        # Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            token_info = token_response.json()
            
            # Get user info using access token
            user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {token_info['access_token']}"}
            user_response = await client.get(user_info_url, headers=headers)
            user_response.raise_for_status()
            user_info = user_response.json()
        
        # Get database connection
        db = get_database()
        users_collection = db.users
        
        # Check if user exists, create if not
        existing_user = await users_collection.find_one({"email": user_info["email"]})
        
        if existing_user:
            user = User(**existing_user)
        else:
            # Create new user
            user = User(
                email=user_info["email"],
                name=user_info.get("name", ""),
                points=0,
                scan_ids=[]
            )
            await users_collection.insert_one(user.dict())
        
        # Create JWT token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                name=user.name,
                points=user.points
            )
        )
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=400, detail=f"Google API error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.get("/me", response_model=UserResponse)
async def get_current_user(payload: dict = Depends(verify_token)):
    """Get current authenticated user info"""
    from bson import ObjectId
    
    db = get_database()
    users_collection = db.users
    
    # Convert string ObjectId to ObjectId object
    user_id = ObjectId(payload["sub"])
    user = await users_collection.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        name=user.get("name", ""),
        points=user.get("points", 0)
    )


@router.post("/refresh")
async def refresh_token(payload: dict = Depends(verify_token)):
    """Refresh JWT token"""
    # Create new token with same user data
    access_token = create_access_token(
        data={"sub": payload["sub"], "email": payload["email"]}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer"
    )
