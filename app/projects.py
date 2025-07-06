from fastapi import APIRouter
from fastui import AnyComponent, FastUI
from fastui import components as c
from fastui.components.display import DisplayMode, DisplayLookup
from fastui.events import GoToEvent, BackEvent
from sqlmodel import select

from .shared import base_page
from .models import Project
from .database import SessionDep

router = APIRouter()

@router.get("/", response_model=FastUI, response_model_exclude_none=True)
def api_index(session: SessionDep, page: int = 1) -> list[AnyComponent]:
    page_size = 20
    projects = session.exec(select(Project)).all()
    return base_page(
        c.Heading(text='Projects', level=2),
        c.Table(
            data=projects[(page - 1) * page_size : page * page_size],
            data_model=Project,
            columns=[
                DisplayLookup(field='name', on_click=GoToEvent(url='/samples/?project_id={id}')),
                DisplayLookup(field='num_samples', title='Samples'),
            ]
        ),
        c.Pagination(page=page, page_size=page_size, total=len(projects)),
    )

