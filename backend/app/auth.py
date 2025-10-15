"""
Authentication system for AstroFinancial API
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

# Security configuration
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

class DatabaseConnection:
    """Database connection manager"""
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                # Fallback for development
                database_url = "postgresql://postgres:password@localhost:5432/astrofinancial"

            self.connection = psycopg2.connect(
                database_url,
                cursor_factory=RealDictCursor
            )
            self.connection.autocommit = True
            logger.info("✓ Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"✗ Failed to connect to database: {e}")
            raise HTTPException(
                status_code=500,
                detail="Database connection failed"
            )

    def get_cursor(self):
        """Get database cursor with reconnection logic"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")  # Test connection
            return cursor
        except:
            # Reconnect and try again
            self.connect()
            return self.connection.cursor()

# Global database connection
db_manager = DatabaseConnection()

class AuthService:
    """Authentication service"""

    def __init__(self):
        self.db = db_manager

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        to_encode.update({
            "exp": expire,
            "jti": str(uuid.uuid4()),  # JWT ID for token tracking
            "iat": datetime.utcnow()
        })
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    async def create_user(self, email: str, password: str, full_name: str,
                         is_admin: bool = False, subscription_tier: str = "basic") -> Dict[str, Any]:
        """Create a new user (admin function)"""
        cursor = self.db.get_cursor()
        try:
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail="User with this email already exists"
                )

            password_hash = self.hash_password(password)
            user_id = str(uuid.uuid4())

            cursor.execute("""
                INSERT INTO users (id, email, password_hash, full_name, is_admin, subscription_tier)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, email, full_name, is_admin, subscription_tier, created_at
            """, (user_id, email, password_hash, full_name, is_admin, subscription_tier))

            user = cursor.fetchone()
            logger.info(f"✓ Created user: {email}")

            return {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "is_admin": user["is_admin"],
                "subscription_tier": user["subscription_tier"],
                "created_at": user["created_at"]
            }
        except psycopg2.Error as e:
            logger.error(f"✗ Database error creating user: {e}")
            raise HTTPException(status_code=500, detail="Failed to create user")

    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user with email and password"""
        cursor = self.db.get_cursor()
        try:
            cursor.execute("""
                SELECT id, email, password_hash, full_name, is_active, is_admin,
                       subscription_tier, api_quota_daily, api_calls_today
                FROM users
                WHERE email = %s
            """, (email,))

            user = cursor.fetchone()
            if not user:
                logger.warning(f"✗ Login attempt for non-existent user: {email}")
                return None

            if not self.verify_password(password, user["password_hash"]):
                logger.warning(f"✗ Invalid password for user: {email}")
                return None

            if not user["is_active"]:
                logger.warning(f"✗ Login attempt for deactivated user: {email}")
                raise HTTPException(
                    status_code=400,
                    detail="Account is deactivated"
                )

            # Update last login
            cursor.execute("""
                UPDATE users SET last_login = NOW() WHERE id = %s
            """, (user["id"],))

            logger.info(f"✓ Successful login: {email}")

            return {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "is_admin": user["is_admin"],
                "subscription_tier": user["subscription_tier"],
                "api_quota_daily": user["api_quota_daily"],
                "api_calls_today": user["api_calls_today"]
            }
        except psycopg2.Error as e:
            logger.error(f"✗ Database error during authentication: {e}")
            raise HTTPException(status_code=500, detail="Authentication failed")

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        cursor = self.db.get_cursor()
        try:
            cursor.execute("""
                SELECT id, email, full_name, is_admin, subscription_tier,
                       api_quota_daily, api_calls_today, quota_reset_date
                FROM users
                WHERE id = %s AND is_active = true
            """, (user_id,))

            user = cursor.fetchone()
            if not user:
                return None

            return dict(user)
        except psycopg2.Error as e:
            logger.error(f"✗ Database error getting user: {e}")
            return None

    async def increment_api_calls(self, user_id: str) -> None:
        """Increment user's daily API call count"""
        cursor = self.db.get_cursor()
        try:
            # Reset counter if it's a new day
            cursor.execute("""
                UPDATE users
                SET
                    api_calls_today = CASE
                        WHEN quota_reset_date < CURRENT_DATE THEN 1
                        ELSE api_calls_today + 1
                    END,
                    quota_reset_date = CURRENT_DATE
                WHERE id = %s
            """, (user_id,))
        except psycopg2.Error as e:
            logger.error(f"✗ Error incrementing API calls: {e}")

# Initialize auth service
auth_service = AuthService()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Dependency to get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as e:
        logger.warning(f"✗ JWT decode error: {e}")
        raise credentials_exception

    user = await auth_service.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception

    return user

async def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency to ensure current user is an admin"""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def check_api_quota(user: Dict[str, Any]) -> None:
    """Check if user has exceeded their daily API quota"""
    if user["api_calls_today"] >= user["api_quota_daily"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily API quota exceeded ({user['api_quota_daily']} calls/day). Quota resets at midnight UTC."
        )

# Search history functions
async def save_search_history(user_id: str, query_text: str, query_type: str,
                             query_params: Dict[str, Any], results: Dict[str, Any]) -> None:
    """Save search to user's history"""
    cursor = db_manager.get_cursor()
    try:
        cursor.execute("""
            INSERT INTO search_history (
                user_id, query_text, query_type, query_params,
                results, results_count, execution_time_ms
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            query_text,
            query_type,
            query_params,
            results,
            results.get("results_count", 0),
            results.get("execution_time_ms", 0)
        ))
        logger.info(f"✓ Saved search history for user {user_id}")
    except psycopg2.Error as e:
        logger.error(f"✗ Error saving search history: {e}")