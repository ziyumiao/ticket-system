from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import BASE_DIR

templates = Jinja2Templates(directory=str(BASE_DIR / "web" / "templates"))
