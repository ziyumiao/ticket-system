import sys
sys.path.insert(0, ".")

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import settings, BASE_DIR
from database.connection import init_db
from api.api_routes import router as api_router
from api.web_routes import router as web_router
from api.dingtalk_routes import router as dingtalk_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "web" / "static")),
    name="static",
)

app.include_router(api_router)
app.include_router(web_router)
app.include_router(dingtalk_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
