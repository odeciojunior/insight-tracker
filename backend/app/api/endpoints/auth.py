from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import EmailStr

from app.core.config import settings
from app.core.logging import get_logger
from app.db.mongodb import get_mongodb, MongoDBClient
from app.schemas.user import UserCreate, UserResponse, UserInDB, Token

logger = get_logger(__name__)
router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    mongodb: MongoDBClient = Depends(get_mongodb)
) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = await mongodb.find_one("users", {"_id": user_id})
    if user is None:
        raise credentials_exception
    return UserInDB(**user)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_create: UserCreate,
    mongodb: MongoDBClient = Depends(get_mongodb)
) -> UserResponse:
    """Register a new user."""
    # Check if email already exists
    if await mongodb.find_one("users", {"email": user_create.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user document
    user_data = user_create.model_dump()
    user_data["hashed_password"] = pwd_context.hash(user_data.pop("password"))
    user_data["created_at"] = datetime.utcnow()
    user_data["is_active"] = True
    
    try:
        user_id = await mongodb.insert_one("users", user_data)
        user = await mongodb.find_one("users", {"_id": user_id})
        return UserResponse(**user)
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    mongodb: MongoDBClient = Depends(get_mongodb)
) -> Token:
    """Login user and return JWT token."""
    # Find user by email
    user = await mongodb.find_one("users", {"email": form_data.username})
    if not user or not pwd_context.verify(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["_id"])},
        expires_delta=access_token_expires
    )
    
    # Set cookie for web clients
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=not settings.DEBUG
    )
    
    return Token(access_token=access_token, token_type="bearer")

@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing the auth cookie."""
    response.delete_cookie("access_token")
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserInDB = Depends(get_current_user)
) -> UserResponse:
    """Get current user information."""
    return UserResponse(**current_user.model_dump())
