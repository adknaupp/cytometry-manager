from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastui import prebuilt_html

from .main import router as main_router
from .samples import router as samples_router
from .projects import router as projects_router
from .search import router as search_router
from .subjects import router as subjects_router
from .cohorts import router as cohorts_router
from .visualizations import router as visualizations_router
from .datasets import router as datasets_router

app = FastAPI()

app.include_router(main_router, prefix="/api")
app.include_router(samples_router, prefix="/api/samples")
app.include_router(projects_router, prefix="/api/projects")
app.include_router(search_router, prefix="/api/search")
app.include_router(subjects_router, prefix="/api/subjects")
app.include_router(cohorts_router, prefix="/api/cohorts")
app.include_router(visualizations_router, prefix="/api/visualizations")
app.include_router(datasets_router, prefix="/api/datasets")

@app.get('/favicon.ico', status_code=404, response_class=PlainTextResponse)
async def favicon_ico() -> str:
    return 'page not found'

@app.get("/{path:path}")
async def html_landing() -> HTMLResponse:
    return HTMLResponse(prebuilt_html(title="Cytometry Manager"))
