from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import jwt
from passlib.context import CryptContext

# This is the line that was failing. 
# Since we fixed config.py in Step 1, this should now work.
from ..config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from ..models.user_models import UserRegister, UserLogin, UserInDB
from ..core.database import get_db_connection

# --- SECURITY CONTEXT AND JWT SETUP ---
auth_router = APIRouter(tags=["Authentication"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login") # Endpoint for getting token

# --- HELPER FUNCTIONS FOR SECURITY ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generates a secure hash for a given password."""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None):
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire, "sub": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- DATABASE / USER UTILS ---

def get_user_by_username(username: str) -> Optional[UserInDB]:
    """Retrieves a user record from the database by username."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        # Map the SQLite row data to the Pydantic model
        return UserInDB(
            id=row['id'],
            username=row['username'],
            password_hash=row['password_hash']
        )
    return None

# --- API ENDPOINTS ---

@auth_router.post("/register", response_model=UserInDB)
async def register(user: UserRegister):
    """Endpoint for new user registration."""
    if get_user_by_username(user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Hash the password before saving
    hashed_password = get_password_hash(user.password)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (user.username, hashed_password)
        )
        conn.commit()
        
        # Retrieve the newly created user to return the full object
        new_user = get_user_by_username(user.username)
        return new_user
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during registration: {e}"
        )
    finally:
        conn.close()


@auth_router.post("/login")
async def login(form_data: UserLogin):
    """Endpoint for user login, returning an access token."""
    user = get_user_by_username(form_data.username)
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate the JWT Access Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": user.id, "username": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}

# --- DEPENDENCY FOR PROTECTED ROUTES ---

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Decodes the JWT token and fetches the current user from the DB."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials (user ID missing)"
            )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials (JWT decode failed)"
        )
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
        
    # We return the user ID and username, sufficient for the application logic
    return {"user_id": row['id'], "username": row['username']}