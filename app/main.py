from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.database import Base, engine
from app.api import auth, management


app = FastAPI()


@app.middleware("http")
async def _log_auth_header(request, call_next):
    # Debug helper: print Authorization header so we can see what Swagger sends
    try:
        auth = request.headers.get("authorization")
        print(f"[DEBUG] Authorization header: {auth}")
    except Exception:
        pass
    response = await call_next(request)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# create tables (safe no-op if already created)
Base.metadata.create_all(bind=engine)

# Include grouped API routers
app.include_router(auth.router)
app.include_router(management.router)
app.include_router(__import__('app.api.transactions', fromlist=['']).router)
app.include_router(__import__('app.api.game_end', fromlist=['']).router)
app.include_router(__import__('app.router.game', fromlist=['']).router)
app.include_router(__import__('app.router.users', fromlist=['']).router)


@app.get("/")
def root():
    return {"message": "LikeBingo API"}


def custom_openapi():    
    app.openapi_schema = None  # force regeneration each time for dev
    openapi_schema = get_openapi(
        title=app.title,
        version="0.1.0",
        routes=app.routes,
    )
    # Add Bearer token security scheme
    openapi_schema.setdefault("components", {})
    openapi_schema["components"].setdefault("securitySchemes", {})
    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    # Optionally require BearerAuth globally in the docs (this only affects docs UI, not runtime)
    openapi_schema.setdefault("security", [{"BearerAuth": []}])

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
