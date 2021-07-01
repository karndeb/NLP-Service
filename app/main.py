from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .library.helpers import *
from app.routers import twoforms, unsplash, accordion, NQR, QE, FR
from starlette.middleware import Middleware
from starlette_context import context, plugins
from starlette_context.middleware import ContextMiddleware
from .middleware import LoggingMiddleware

middleware = [
    Middleware(
        ContextMiddleware,
        plugins=(
            plugins.RequestIdPlugin(),
            plugins.CorrelationIdPlugin(),
            # plugins.FilenamePlugin()
        )
    ),
    Middleware(LoggingMiddleware)
]


app = FastAPI(debug=True, middleware=middleware)


templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(unsplash.router)
app.include_router(twoforms.router)
app.include_router(accordion.router)
app.include_router(NQR.router)
app.include_router(QE.router)
app.include_router(FR.router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    data = openfile("home.md")
    return templates.TemplateResponse("page.html", {"request": request, "data": data})


@app.get("/page/{page_name}", response_class=HTMLResponse)
async def show_page(request: Request, page_name: str):
    data = openfile(page_name+".md")
    return templates.TemplateResponse("page.html", {"request": request, "data": data})


@app.on_event("startup")
async def startup_event() -> None:
    from .setup_logging import setup_logging

    setup_logging()


# @app.get("/")
# async def index(request: Request):
#     context["something else"] = "This will be visible even in the response log"
#     return print(JSONResponse(context.))



