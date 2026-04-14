from fastapi import Request, status
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
import os

SECRET_KEY = os.getenv("JWT_SECRET", "bravado-secret-2026")

async def tenant_context_middleware(request: Request, call_next):
    # 1. Define Public Paths
    public_paths = ["/health", "/auth/token", "/auth/signup", "/webhooks"]
    
    # Check if current path starts with any public path (handles sub-routes)
    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)

    # 2. Extraction & Validation
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Missing or invalid authorization header"}
        )

    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        tenant_id = payload.get("tenant_id")
        if not tenant_id:
            raise JWTError("Missing tenant_id")
            
        # Inject into state for global access
        request.state.tenant_id = tenant_id
        
    except (JWTError, Exception):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or expired session"}
        )

    return await call_next(request)