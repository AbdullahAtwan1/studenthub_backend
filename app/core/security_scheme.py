from fastapi.security import APIKeyHeader

# ✅ Defines Bearer token header for Swagger and all routers
api_key_scheme = APIKeyHeader(name="Authorization", auto_error=False)
