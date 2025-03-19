from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import create_access_token, verify_password, get_password_hash
from app.models.user import User
from app.db.mongodb import get_mongodb
from app.db.redis import get_redis
from app.core.config import settings

router = APIRouter()

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return JWT token."""
    mongodb = await get_mongodb()
    user_doc = await mongodb.find_one(
        "users",
        {"email": form_data.username}
    )
    
    if not user_doc or not verify_password(form_data.password, user_doc["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = User(**user_doc)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/register", response_model=User)
async def register(user_create: UserCreate):
    """Register new user."""
    mongodb = await get_mongodb()
    
    # Check if user exists
    if await mongodb.find_one("users", {"email": user_create.email}):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create user
    user_dict = user_create.dict()
    user_dict["hashed_password"] = get_password_hash(user_create.password)
    del user_dict["password"]
    
    user_id = await mongodb.insert_one("users", user_dict)
    return User(**user_dict, id=user_id)
