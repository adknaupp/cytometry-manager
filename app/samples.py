from typing import Annotated
from fastapi import APIRouter, HTTPException
from fastui import AnyComponent, FastUI
from fastui import components as c
from fastui.events import PageEvent, GoToEvent, BackEvent
from fastui.components.display import DisplayLookup
from fastui.forms import fastui_form
from pydantic import BaseModel, Field
from sqlmodel import select

from .shared import base_page
from .models import Project, Sample, SampleForm
from .database import SessionDep, add_sample

router = APIRouter()

class FilterForm(BaseModel):
    # country: str = Field(json_schema_extra={'search_url': '/api/forms/search', 'placeholder': 'Filter by Country...'})
    project_id: str | None = Field(json_schema_extra={'search_url': '/api/search/projects', 'placeholder': 'Filter by Project...'})
    sample_type: str | None = Field(json_schema_extra={'search_url': '/api/search/sample-types', 'placeholder': 'Filter by Type...'})
    sample_name: str | None = Field(json_schema_extra={'placeholder': 'Filter by Name...'})

@router.get("/", response_model=FastUI, response_model_exclude_none=True)
def samples_index(
        session: SessionDep, 
        page: int = 1,
        project_id: int | None = None,
        sample_type: str | None = None,
        sample_name: str | None = None
    ) -> list[AnyComponent]:
    page_size = 20

    project_name = None
    if project_id:
        project = session.exec(select(Project).where(Project.id == project_id)).first()
        project_name = project.name if project else None
    
    filter_form_initial = {}
    if project_id:
        filter_form_initial['project_id'] = {'value': project_id, 'label': project_name}
    if sample_type:
        filter_form_initial['sample_type'] = {'value': sample_type, 'label': sample_type}
    if sample_name:
        filter_form_initial['sample_name'] = {'value': sample_name, 'label': sample_name}
    
    query = select(Sample)
    if project_id:
        query = query.where(Sample.project_id == project_id)
    if sample_type:
        query = query.where(Sample.type == sample_type)
    if sample_name:
        query = query.where(Sample.name.ilike(f"{sample_name}%"))
    
    samples = session.exec(query).all()

    return base_page(
        c.Heading(text='Samples', level=2),
        c.Button(text='New sample', on_click=PageEvent(name='modal-new-sample')),
        c.Paragraph(text=f'Showing {len(samples)} samples'),
        c.ModelForm(
            model=FilterForm,
            submit_url='.',
            initial=filter_form_initial,
            method='GOTO',
            submit_on_change=True,
            display_mode='inline',
        ),
        c.Modal(
            title='Add new sample',
            body=[
                c.ModelForm(
                    model=SampleForm,
                    submit_url='/api/samples/new',
                    submit_trigger=PageEvent(name='post-new-sample'),
                    footer=[]
                ),
            ],
            footer=[
                c.Button(
                    text='Cancel', 
                    named_style='secondary', 
                    on_click=PageEvent(name='modal-new-sample', clear=True)
                ),
                c.Button(text='Submit', on_click=PageEvent(name='post-new-sample')),
            ],
            open_trigger=PageEvent(name='modal-new-sample'),
        ),
        c.Table(
            data=samples[(page - 1) * page_size : page * page_size],
            data_model=Sample,
            no_data_message="No samples found. Are filters applied?",
            columns=[
                DisplayLookup(
                    field='name', 
                    on_click=GoToEvent(url='/samples/{id}'),
                ),
                DisplayLookup(field='type'),
                DisplayLookup(field='time_from_treatment_start'),
                DisplayLookup(field='b_cell'),
                DisplayLookup(field='cd8_t_cell'),
                DisplayLookup(field='cd4_t_cell'),
                DisplayLookup(field='nk_cell'),
                DisplayLookup(field='monocyte'),
            ],
        ),
        c.Pagination(page=page, page_size=page_size, total=len(samples)),
    )

@router.post("/new", response_model=FastUI, response_model_exclude_none=True)
def submit_sample(form: Annotated[SampleForm, fastui_form(SampleForm)], session: SessionDep) -> list[AnyComponent]:
    add_sample(form, session)
    return [c.FireEvent(event=PageEvent(name='modal-new-sample', clear=True))]


@router.get("/{id}", response_model=FastUI, response_model_exclude_none=True)
def view_sample(id: str, session: SessionDep) -> list[AnyComponent]:
    sample = session.exec(select(Sample).where(Sample.id == id)).first()
    if not sample:
        return base_page(
            c.Heading(text='Sample Not Found', level=2),
            c.Text(text='The requested sample does not exist.'),
        )
    return base_page(
        c.Heading(text='Details for ' + sample.name),
        c.Details(
            data=sample,
        ),
        c.Modal(
            title='Delete Sample',
            body=[
                c.Text(text=f'Are you sure you want to delete the sample "{sample.name}"? This action cannot be undone.'),
            ],
            footer=[
                c.Button(
                    text='Cancel', 
                    named_style='secondary', 
                    on_click=PageEvent(name='modal-delete-sample', clear=True)
                ),
                c.Button(
                    text='Delete', 
                    named_style='warning',
                    on_click=GoToEvent(url=f'/samples/delete/{sample.id}')
                ),
            ],
            open_trigger=PageEvent(name='modal-delete-sample'),
        ),
        c.Button(
            text='Delete Sample',
            named_style='warning',
            on_click=PageEvent(name='modal-delete-sample')
        ),
    )

# there's no way to do DELETE with FastUI, so we use a hack. Only exception is 
# ServerLoad (only when sse=True, see https://github.com/pydantic/FastUI/issues/351), 
# but then it fires immediately, not just when triggered
@router.get("/delete/{id}", response_model=FastUI, response_model_exclude_none=True)
def delete_sample(id: int, session: SessionDep) -> list[AnyComponent]:
    # Find the sample
    db_sample = session.exec(select(Sample).where(Sample.id == id)).first()
    if not db_sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    session.delete(db_sample)
    session.commit()
    return [
        c.FireEvent(event=PageEvent(name='modal-delete-sample', clear=True)),
        c.FireEvent(event=GoToEvent(url='/samples/'))
    ]
