from typing import Annotated, Literal, TypeAlias
from fastapi import APIRouter
from fastui import components as c
from fastui import AnyComponent, FastUI
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent, PageEvent
from fastui.forms import fastui_form
from sqlmodel import select

from app.database import SessionDep, add_cohort
from app.models import Cohort, CohortForm, DatasetForm, Sample, Subject
from app.shared import base_page

router = APIRouter()


@router.get("/", response_model=FastUI, response_model_exclude_none=True)
def api_index(session: SessionDep, page: int = 1) -> list[AnyComponent]:
    page_size = 20
    cohorts = session.exec(select(Cohort)).all()
    return base_page(
        c.Heading(text='Cohorts', level=2),
        c.Paragraph(text=f'To create a new cohort, visit the Subjects page'),
        c.Table(
            data=cohorts[(page - 1) * page_size: page * page_size],
            data_model=Cohort,
            columns=[
                DisplayLookup(field='name', on_click=GoToEvent(url='/cohorts/{id}/details')),
                DisplayLookup(field='condition'),
                DisplayLookup(field='sex'),
                DisplayLookup(field='treatment'),
            ]
        )
    )

@router.post("/new", response_model=FastUI, response_model_exclude_none=True)
def new_cohort(form: Annotated[CohortForm, fastui_form(CohortForm)], session: SessionDep) -> list[AnyComponent]:
    add_cohort(form, session)
    return [
        c.FireEvent(event=PageEvent(name='modal-new-cohort', clear=True)),
    ]

CohortViewKind: TypeAlias = Literal['details', 'samples', 'subjects']

@router.get('/{id}/{kind}', response_model=FastUI, response_model_exclude_none=True)
def cohort_view(id: int, kind: CohortViewKind, session: SessionDep) -> list[AnyComponent]:
    cohort = session.get(Cohort, id)
    if not cohort:
        return base_page(
            c.Heading(text='Cohort not found', level=2),
            c.Paragraph(text='The requested cohort does not exist.')
        )
    return base_page(
        c.Heading(text=f'Cohort: {cohort.name}', level=2),
        c.LinkList(
            links=[
                c.Link(
                    components=[c.Text(text='Details')],
                    on_click=PageEvent(
                        name='change-content', 
                        push_path=f'/cohorts/{id}/details', 
                        context={
                            'kind': 'details',
                            'id': id
                        }
                    ),
                    active=f'/cohorts/{id}/details',
                ),
                c.Link(
                    components=[c.Text(text='Samples')],
                    on_click=PageEvent(
                        name='change-content', 
                        push_path=f'/cohorts/{id}/samples', 
                        context={
                            'kind': 'samples',
                            'id': id
                        }
                    ),
                    active=f'/cohorts/{id}/samples',
                ),
                c.Link(
                    components=[c.Text(text='Subjects')],
                    on_click=PageEvent(
                        name='change-content', 
                        push_path=f'/cohorts/{id}/subjects', 
                        context={
                            'kind': 'subjects',
                            'id': id
                        }
                    ),
                    active=f'/cohorts/{id}/subjects',
                ),
            ],
            mode='tabs',
            class_name='+ mb-4',
        ),
        c.ServerLoad(
            path='/cohorts/content/{id}/{kind}',
            load_trigger=PageEvent(name='change-content'),
            components=cohort_content(id, kind, session),
        ),
    )

@router.get('/content/{id}/{kind}', response_model=FastUI, response_model_exclude_none=True)
def cohort_content(
        id: int, 
        kind: CohortViewKind, 
        session: SessionDep, 
        page: int = 1,
    ) -> list[AnyComponent]:
    cohort = session.get(Cohort, id)
    match kind:
        case 'details':
            return [
                c.Details(data=cohort)
            ]
        case 'samples':
            page_size = 20
            subjects = cohort.get_subjects(session)
            query = select(Sample).where(Sample.subject_id.in_([s.id for s in subjects]))
            samples = session.exec(query).all()
            return [
                c.Button(
                    text='New Dataset',
                    on_click=PageEvent(name='modal-new-dataset'),
                ),
                c.Paragraph(text=f'There are {len(samples)} samples associated with subjects in this cohort.'),
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
                c.Modal( # TODO: form should not include a field for cohort. Cohort should be pre-filled. That, or this form should be moved to the Dataset page.
                    title="New Dataset",
                    body=[
                        c.ModelForm(
                            model=DatasetForm,
                            submit_url='/api/datasets/new',
                            submit_trigger=PageEvent(name='post-new-dataset'),
                            footer=[]
                        ),
                    ],
                    footer=[
                        c.Button(
                            text='Cancel', 
                            named_style='secondary', 
                            on_click=PageEvent(name='modal-new-dataset', clear=True)
                        ),
                        c.Button(text='Submit', on_click=PageEvent(name='post-new-dataset')),
                    ],
                    open_trigger=PageEvent(name='modal-new-dataset'),
                ),
                c.Pagination(page=page, page_size=page_size, total=len(samples)),
            ]
        case 'subjects':
            subjects = cohort.get_subjects(session)
            return [
                c.Paragraph(text=f'There are {len(subjects)} subjects in this cohort.'),
                c.Table(
                    data=subjects, # TODO: paginate this
                    data_model=Subject,
                    no_data_message="No subjects in this cohort.",
                    columns=[
                        DisplayLookup(field='name', on_click=GoToEvent(url='/subjects/{id}')),
                        DisplayLookup(field='sex'),
                        DisplayLookup(field='response'),
                        DisplayLookup(field='treatment'),
                        DisplayLookup(field='age'),
                        DisplayLookup(field='condition'),
                    ]
                ),
            ]
        case _:
            raise ValueError(f'Invalid kind {kind!r}')
