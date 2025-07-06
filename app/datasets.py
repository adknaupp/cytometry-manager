from typing import Annotated, Literal, TypeAlias
from fastapi import APIRouter
from fastui import components as c
from fastui import AnyComponent, FastUI
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent, PageEvent
from fastui.forms import fastui_form
from sqlmodel import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.database import SessionDep, add_dataset
from app.models import Cohort, Dataset, DatasetForm, DatasetSampleFilterForm, Subject, ResponseEnum
from app.shared import base_page

router = APIRouter()

class DatasetRow(BaseModel):
    id: int | None = None # make all fields optional to avoid trivial errors
    name: str | None = None
    sample_type: str | None = None
    cohort_name: str | None = None
    time_from_treatment_start: int | None = None

@router.get("/", response_model=FastUI, response_model_exclude_none=True)
def api_index(session: SessionDep, page: int = 1) -> list[AnyComponent]:
    page_size = 20
    datasets = session.exec(select(Dataset).options(selectinload(Dataset.cohort))).all()
    dataset_rows = []
    for dataset in datasets:
        cohort_name = dataset.cohort.name if dataset.cohort else 'Unknown'
        dataset_rows.append(DatasetRow(
            id=dataset.id,
            name=dataset.name,
            cohort_name=cohort_name,
            sample_type=dataset.sample_type,
            time_from_treatment_start=dataset.time_from_treatment_start
        ))
    return base_page(
        c.Heading(text='Datasets', level=2),
        c.Paragraph(text=f'To create a new dataset, visit the Cohorts page, select a cohort, and visit the "Samples" tab.'),
        c.Table(
            data=dataset_rows[(page - 1) * page_size: page * page_size],
            data_model=DatasetRow,
            columns=[
                DisplayLookup(field='name', on_click=GoToEvent(url='/datasets/{id}/details')),
                DisplayLookup(field='sample_type'),
                DisplayLookup(field='cohort_name', title='Cohort', on_click=GoToEvent(url='/cohorts/{cohort_id}/details')),
                DisplayLookup(field='time_from_treatment_start', title='Time from Treatment Start'),
            ]
        )
    )

@router.post("/new", response_model=FastUI, response_model_exclude_none=True)
def new_dataset(form: Annotated[DatasetForm, fastui_form(DatasetForm)], session: SessionDep) -> list[AnyComponent]:
    add_dataset(form, session)
    return [
        c.FireEvent(event=PageEvent(name='modal-new-dataset', clear=True)),
        c.FireEvent(event=GoToEvent(url='/datasets/'))
    ]

DatasetViewKind: TypeAlias = Literal['details', 'samples', 'visualizations']

@router.get('/{id}/{kind}', response_model=FastUI, response_model_exclude_none=True)
def dataset_view(
    id: int, 
    kind: DatasetViewKind, 
    session: SessionDep,
    response: str | None = None,
    sex: str | None = None,
    page: int = 1
) -> list[AnyComponent]:
    dataset = session.get(Dataset, id)
    if not dataset:
        return base_page(
            c.Heading(text='Dataset not found', level=2),
            c.Paragraph(text='The requested dataset does not exist.')
        )
    
    return base_page(
        c.Heading(text=f'Dataset: {dataset.name}', level=2),
        c.LinkList(
            links=[
                c.Link(
                    components=[c.Text(text='Details')],
                    on_click=PageEvent(
                        name='change-content', 
                        push_path=f'/datasets/{id}/details', 
                        context={
                            'kind': 'details',
                            'id': id
                        }
                    ),
                    active=f'/datasets/{id}/details',
                ),
                c.Link(
                    components=[c.Text(text='Samples')],
                    on_click=PageEvent(
                        name='change-content', 
                        push_path=f'/datasets/{id}/samples', 
                        context={
                            'kind': 'samples',
                            'id': id
                        }
                    ),
                    active=f'/datasets/{id}/samples',
                ),
                c.Link(
                    components=[c.Text(text='Visualizations')],
                    on_click=PageEvent(
                        name='change-content', 
                        push_path=f'/datasets/{id}/visualizations', 
                        context={
                            'kind': 'visualizations',
                            'id': id
                        }
                    ),
                    active=f'/datasets/{id}/visualizations',
                )
            ],
            mode='tabs',
            class_name='+ mb-4',
        ),
        c.ServerLoad(
            path='/datasets/content/{id}/{kind}',
            load_trigger=PageEvent(name='change-content'),
            components=dataset_content(id, kind, session, response, sex, page),
        )
    )

class DatasetDetails(BaseModel):
    id: int | None = None
    name: str | None = None
    cohort_id: int | None = None
    cohort_name: str | None = None
    sample_type: str | None = None
    time_from_treatment_start: int | None = None

class DatasetSampleRow(BaseModel):
    id: int | None = None
    name: str | None = None
    subject_id: int | None = None
    subject_name: str | None = None
    sex: str | None = None
    response: str | None = None

@router.get('/content/{id}/{kind}', response_model=FastUI, response_model_exclude_none=True)
def dataset_content(
        id: int, 
        kind: DatasetViewKind, 
        session: SessionDep,
        response: str | None = None,  # for filtering samples
        sex: str | None = None,
        page: int = 1,
    ) -> list[AnyComponent]:
    dataset = session.get(Dataset, id)
    if not dataset:
        return base_page(
            c.Heading(text='Dataset not found', level=2),
            c.Paragraph(text='The requested dataset does not exist.')
        )

    match kind:
        case 'details':
            cohort = session.get(Cohort, dataset.cohort_id)
            cohort_name = cohort.name if cohort else 'Unknown'
            dataset_details = DatasetDetails(
                id=dataset.id,
                name=dataset.name,
                cohort_name=cohort_name,
                sample_type=dataset.sample_type,
                time_from_treatment_start=dataset.time_from_treatment_start
            )
            return [
                c.Details(
                    data=dataset_details,
                    fields=[
                        DisplayLookup(field='name'),
                        DisplayLookup(field='cohort_name', title='Cohort', on_click=GoToEvent(url='/cohorts/{id}/details')),
                        DisplayLookup(field='sample_type'),
                        DisplayLookup(field='time_from_treatment_start')
                    ]
                )
            ]
        case 'samples': # FIXME: filtering doesn't work
            page_size = 20
            samples = dataset.get_samples(session) # TODO: performance (perceptable lag on UI)
            sample_rows = []
            for sample in samples: # TODO: performance (perceptable lag on UI)
                subject = session.get(Subject, sample.subject_id)
                sample_response = subject.response.value if subject and subject.response else None
                if response and sample_response != response: # filter by response
                    continue
                sample_sex = subject.sex.value if subject and subject.sex else None
                if sex and sample_sex != sex: # filter by sex
                    continue
                sample_rows.append(DatasetSampleRow(
                    id=sample.id,
                    name=sample.name,
                    subject_id=sample.subject_id,
                    subject_name=subject.name if subject else 'Unknown',
                    sex=sample_sex,
                    response=sample_response
                ))
            filter_form_initial = {}
            if sex:
                filter_form_initial['sex'] = sex
            if response:
                filter_form_initial['response'] = response
            return [
                c.Paragraph(text=f'There are {len(samples)} samples associated with this dataset (currently showing {len(sample_rows)} after filtering).'),
                c.ModelForm(
                    model=DatasetSampleFilterForm,
                    submit_url='.',
                    initial=filter_form_initial,
                    method='GOTO',
                    submit_on_change=True,
                    display_mode='inline',
                ),
                c.Table(
                    data=sample_rows[(page - 1) * page_size : page * page_size],
                    data_model=DatasetSampleRow,
                    columns=[
                        DisplayLookup(field='name', on_click=GoToEvent(url='/samples/{id}')),
                        DisplayLookup(field='subject_name', title='Subject', on_click=GoToEvent(url='/subjects/{subject_id}')),
                        DisplayLookup(field='sex'),
                        DisplayLookup(field='response'),
                    ]
                ),
                c.Pagination(page=page, page_size=page_size, total=len(sample_rows)),
            ]
        case 'visualizations':
            return [
                c.Image(
                    src=f'/api/visualizations/dataset/{id}',
                )
            ]
        case _:
            raise ValueError(f'Invalid kind {kind!r}')
