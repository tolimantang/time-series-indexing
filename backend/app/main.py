"""
AstroFinancial API Server with Authentication
Production-ready FastAPI application
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
import uvicorn

# Import our modules
from auth import (
    auth_service, get_current_user, get_admin_user,
    check_api_quota, save_search_history
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="AstroFinancial API",
    description="AI-powered astronomical pattern analysis for financial markets",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev
        "https://*.vercel.app",   # Vercel deployments
        "https://yourdomain.com", # Your production domain
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Pydantic models
class LoginRequest(BaseModel):
    email: str = Field(..., example="demo@astrofinancial.com")
    password: str = Field(..., example="user123")

class CreateUserRequest(BaseModel):
    email: str = Field(..., example="newuser@example.com")
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., example="John Doe")
    is_admin: bool = Field(default=False)
    subscription_tier: str = Field(default="basic", regex="^(basic|premium|enterprise)$")

class SemanticQueryRequest(BaseModel):
    query: str = Field(..., example="Saturn in Capricorn with Mercury retrograde")
    max_results: int = Field(default=10, ge=1, le=50)
    collection_name: str = Field(default="astronomical_detailed")
    include_market_data: bool = Field(default=False)

class PatternAnalysisRequest(BaseModel):
    query: str = Field(..., example="Moon conjunct Saturn")
    lookback_days: int = Field(default=30, ge=1, le=365)
    target_assets: List[str] = Field(default=["SPY", "VIX", "EURUSD"])

class SearchHistoryResponse(BaseModel):
    id: str
    query_text: str
    query_type: str
    results_count: int
    created_at: datetime
    is_saved: bool
    tags: List[str]

# Import your existing API logic
try:
    import sys
    sys.path.append('/Users/yetang/Development/time-series-indexing')
    from api_server import AstroFinancialAPI
    from astro_embedding_pipeline import AstroEmbeddingPipeline

    # Initialize the API with your existing logic
    pipeline = AstroEmbeddingPipeline()
    api_instance = AstroFinancialAPI()
    logger.info("✓ AstroFinancial API components initialized")
except Exception as e:
    logger.error(f"✗ Failed to initialize API components: {e}")
    # Create mock for development
    class MockAPI:
        def semantic_search(self, request):
            return {
                "query_type": "semantic_search",
                "results_count": 0,
                "results": [],
                "execution_time_ms": 0,
                "metadata": {"query": request.query}
            }
    api_instance = MockAPI()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AstroFinancial API",
        "version": "1.0.0",
        "docs": "/docs" if os.getenv("ENVIRONMENT") != "production" else "disabled"
    }

# Authentication endpoints
@app.post("/auth/login")
async def login(request: LoginRequest):
    """User login endpoint"""
    try:
        user = await auth_service.authenticate_user(request.email, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        access_token = auth_service.create_access_token(data={"sub": str(user["id"])})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 86400,  # 24 hours
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "subscription_tier": user["subscription_tier"],
                "api_quota_daily": user["api_quota_daily"],
                "api_calls_today": user["api_calls_today"]
            }
        }
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/auth/admin/create-user")
async def create_user(
    request: CreateUserRequest,
    current_user: Dict[str, Any] = Depends(get_admin_user)
):
    """Create a new user (admin only)"""
    try:
        user = await auth_service.create_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            is_admin=request.is_admin,
            subscription_tier=request.subscription_tier
        )
        logger.info(f"Admin {current_user['email']} created user {request.email}")
        return {"message": "User created successfully", "user": user}
    except Exception as e:
        logger.error(f"User creation error: {e}")
        raise

@app.get("/auth/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    return {
        "user": {
            "id": current_user["id"],
            "email": current_user["email"],
            "full_name": current_user["full_name"],
            "subscription_tier": current_user["subscription_tier"],
            "api_quota_daily": current_user["api_quota_daily"],
            "api_calls_today": current_user["api_calls_today"]
        }
    }

# Protected API endpoints
@app.post("/query/semantic")
async def semantic_search(
    request: SemanticQueryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Perform semantic search (authenticated)"""
    # Check API quota
    check_api_quota(current_user)

    try:
        # Perform the search using your existing logic
        start_time = datetime.now()

        # Call your existing API
        results = api_instance.semantic_search(request)

        # Save to search history
        await save_search_history(
            user_id=current_user["id"],
            query_text=request.query,
            query_type="semantic_search",
            query_params=request.dict(),
            results=results if isinstance(results, dict) else results.__dict__
        )

        # Update API call count
        await auth_service.increment_api_calls(current_user["id"])

        logger.info(f"Semantic search by {current_user['email']}: '{request.query}'")

        return results

    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/analysis/pattern")
async def pattern_analysis(
    request: PatternAnalysisRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Perform pattern analysis (authenticated)"""
    # Check API quota
    check_api_quota(current_user)

    try:
        # Call your existing pattern analysis
        results = api_instance.pattern_analysis(request)

        # Save to search history
        await save_search_history(
            user_id=current_user["id"],
            query_text=request.query,
            query_type="pattern_analysis",
            query_params=request.dict(),
            results=results if isinstance(results, dict) else results.__dict__
        )

        # Update API call count
        await auth_service.increment_api_calls(current_user["id"])

        logger.info(f"Pattern analysis by {current_user['email']}: '{request.query}'")

        return results

    except Exception as e:
        logger.error(f"Pattern analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/user/search-history")
async def get_search_history(
    page: int = 1,
    limit: int = 20,
    query_type: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user's search history"""
    from auth import db_manager

    cursor = db_manager.get_cursor()
    try:
        offset = (page - 1) * limit

        where_clause = "WHERE user_id = %s"
        params = [current_user["id"]]

        if query_type:
            where_clause += " AND query_type = %s"
            params.append(query_type)

        # Get paginated history
        cursor.execute(f"""
            SELECT id, query_text, query_type, results_count, created_at, is_saved, tags
            FROM search_history
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])

        history = cursor.fetchall()

        # Get total count
        cursor.execute(f"""
            SELECT COUNT(*) FROM search_history {where_clause}
        """, params)
        total = cursor.fetchone()[0]

        return {
            "history": [
                {
                    "id": h["id"],
                    "query_text": h["query_text"],
                    "query_type": h["query_type"],
                    "results_count": h["results_count"],
                    "created_at": h["created_at"],
                    "is_saved": h["is_saved"],
                    "tags": h["tags"] or []
                } for h in history
            ],
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            }
        }
    except Exception as e:
        logger.error(f"Error fetching search history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch search history")

@app.get("/user/search-history/{search_id}")
async def get_search_details(
    search_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get detailed search results"""
    from auth import db_manager

    cursor = db_manager.get_cursor()
    try:
        cursor.execute("""
            SELECT query_text, query_type, query_params, results, created_at, execution_time_ms, tags
            FROM search_history
            WHERE id = %s AND user_id = %s
        """, (search_id, current_user["id"]))

        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Search not found")

        return {
            "id": search_id,
            "query_text": result["query_text"],
            "query_type": result["query_type"],
            "query_params": result["query_params"],
            "results": result["results"],
            "created_at": result["created_at"],
            "execution_time_ms": result["execution_time_ms"],
            "tags": result["tags"] or []
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching search details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch search details")

@app.get("/query/examples")
async def get_query_examples():
    """Get example queries (public endpoint)"""
    return {
        "semantic_queries": [
            "Saturn in Capricorn with Mercury retrograde",
            "Moon conjunct Jupiter in Cancer",
            "Mars opposition Neptune with tight aspects",
            "Multiple planetary conjunctions",
            "Venus in Gemini during lunar eclipse",
            "Jupiter trine Saturn harmonious aspects"
        ],
        "pattern_analysis_examples": [
            {
                "query": "Saturn conjunct Pluto",
                "lookback_days": 90,
                "target_assets": ["SPY", "VIX", "GOLD"]
            },
            {
                "query": "Mercury retrograde in fire signs",
                "lookback_days": 30,
                "target_assets": ["EURUSD", "GBPUSD"]
            }
        ]
    }

# Admin endpoints
@app.get("/admin/users")
async def list_users(
    page: int = 1,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_admin_user)
):
    """List all users (admin only)"""
    from auth import db_manager

    cursor = db_manager.get_cursor()
    try:
        offset = (page - 1) * limit

        cursor.execute("""
            SELECT id, email, full_name, subscription_tier, api_quota_daily,
                   api_calls_today, created_at, last_login, is_active
            FROM users
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))

        users = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]

        return {
            "users": [dict(user) for user in users],
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            }
        }
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")

@app.get("/admin/analytics")
async def get_analytics(
    current_user: Dict[str, Any] = Depends(get_admin_user)
):
    """Get system analytics (admin only)"""
    from auth import db_manager

    cursor = db_manager.get_cursor()
    try:
        # Basic stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_users,
                COUNT(*) FILTER (WHERE last_login > NOW() - INTERVAL '7 days') as active_users_7d,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') as new_users_30d
            FROM users
        """)
        user_stats = cursor.fetchone()

        # Search stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_searches,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as searches_24h,
                AVG(execution_time_ms) as avg_execution_time,
                COUNT(DISTINCT user_id) as unique_users_searching
            FROM search_history
        """)
        search_stats = cursor.fetchone()

        return {
            "users": dict(user_stats),
            "searches": dict(search_stats),
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT") != "production"
    )