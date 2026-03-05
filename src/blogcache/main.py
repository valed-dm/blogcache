from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .api import posts
from .core.config import settings
from .core.database import engine
from .models import post


# Just for development
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(post.Base.metadata.create_all)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
    on_startup=[create_tables],
)

app.include_router(posts.router)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.app_name}
