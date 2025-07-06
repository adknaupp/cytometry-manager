from typing import Annotated, Literal
from fastapi import APIRouter
from fastui import AnyComponent, FastUI
from fastui import components as c
from fastui.components.display import DisplayMode, DisplayLookup
from fastui.events import GoToEvent, BackEvent, PageEvent
from fastui.forms import fastui_form
from sqlmodel import select

from .shared import base_page
from .models import Subject, SubjectForm, SubjectFilterForm, CohortForm
from .database import SessionDep, add_subject

router = APIRouter()

@router.get("/", response_model=FastUI, response_model_exclude_none=True)
def api_index(
        session: SessionDep, 
        page: int = 1,
        response: str | None = None,
        sex: str | None = None,
        treatment: str | None = None,
        name: str | None = None,
    ) -> list[AnyComponent]:
    page_size = 20

    filter_form_initial = {}
    if sex:
        filter_form_initial['sex'] = {'value': sex, 'label': sex}
    if response:
        filter_form_initial['response'] = {'value': response, 'label': response}
    if name:
        filter_form_initial['name'] = {'value': name, 'label': name}
    if treatment:
        filter_form_initial['treatment'] = {'value': treatment, 'label': treatment}

    cohort_form_initial = filter_form_initial.copy()
    cohort_form_initial.pop('name', None)

    query = select(Subject)
    if sex:
        query = query.where(Subject.sex == sex)
    if response:
        query = query.where(Subject.response == response)
    if treatment:
        query = query.where(Subject.treatment == treatment)
    if name:
        query = query.where(Subject.name.ilike(f"{name}%"))
    subjects = session.exec(query).all()

    return base_page(
        c.Div(
            components=[
                c.Heading(text='Subjects', level=2),
                c.Button(
                    text='New subject', 
                    on_click=PageEvent(name='modal-new-subject'),
                ),
                c.Button(
                    text='New Cohort', 
                    on_click=PageEvent(name='modal-new-cohort'),
                    class_name='+ ms-2',
                ),
                c.Button(
                    text='Clear all filters', 
                    named_style='secondary', 
                    on_click=GoToEvent(url='/subjects/'),
                    class_name='+ ms-2',
                ),
                c.Paragraph(text=f'Showing {len(subjects)} subjects'),
            ]
        ),
        c.Modal(
            title="New Cohort",
            body=[
                # c.Paragraph(text=f'Save this cohort of {len(subjects)} subjects'), # TODO: include this when the below issue is resolved.
                c.Paragraph(
                    text="Optional fields left empty will be set to 'Any'."
                ),
                c.ModelForm( # TODO: might want to use c.Details instead?
                    model=CohortForm,
                    submit_url='/api/cohorts/new',
                    initial=cohort_form_initial, # TODO: this not populating the form. cohort_form_initial is empty, as evidenced by the value [object Object] in the form
                    submit_trigger=PageEvent(name='post-new-cohort'),
                    footer=[],
                )
            ],
            footer=[
                c.Button(
                    text='Cancel', 
                    named_style='secondary', 
                    on_click=PageEvent(name='modal-new-cohort', clear=True)
                ),
                c.Button(text='Submit', on_click=PageEvent(name='post-new-cohort')),
            ],
            open_trigger=PageEvent(name='modal-new-cohort'),
        ),
        c.ModelForm(
            model=SubjectFilterForm,
            submit_url='.',
            initial=filter_form_initial,
            method='GOTO',
            submit_on_change=True,
            display_mode='inline',
        ),
        c.Table(
            data=subjects[(page - 1) * page_size : page * page_size],
            data_model=Subject,
            no_data_message="No subjects found. Are filters applied?",
            columns=[
                DisplayLookup(field='name', on_click=GoToEvent(url='/subjects/{id}')),
                DisplayLookup(field='sex'),
                DisplayLookup(field='response'),
                DisplayLookup(field='treatment'),
                DisplayLookup(field='age'),
                DisplayLookup(field='condition'),
                DisplayLookup(field='time_from_treatment_start')
            ]
        ),
        c.Pagination(page=page, page_size=page_size, total=len(subjects)),
        c.Modal(
            title="New Subject",
            body=[
                c.ModelForm(
                    model=SubjectForm,
                    submit_url='/api/subjects/new',
                    submit_trigger=PageEvent(name='post-new-subject'),
                    footer=[]
                )
            ],
            footer=[
                c.Button(
                    text='Cancel', 
                    named_style='secondary', 
                    on_click=PageEvent(name='modal-new-subject', clear=True)
                ),
                c.Button(text='Submit', on_click=PageEvent(name='post-new-subject')),
            ],
            open_trigger=PageEvent(name='modal-new-subject'),
        )
    )

@router.post("/new", response_model=FastUI, response_model_exclude_none=True)
def new_subject(form: Annotated[SubjectForm, fastui_form(SubjectForm)], session: SessionDep) -> list[AnyComponent]:
    add_subject(form, session)
    return [c.FireEvent(event=PageEvent(name='modal-new-subject', clear=True))]

@router.get("/{id}", response_model=FastUI, response_model_exclude_none=True)
def subject_view(id: int, session: SessionDep) -> list[AnyComponent]:
    subject = session.get(Subject, id)
    if not subject:
        return base_page(
            c.Heading(text='Subject not found', level=2),
            c.Paragraph(text='The requested subject does not exist.')
        )
    return base_page(
        c.Heading(text=f'Subject: {subject.name}', level=2),
        c.Details(data=subject)
    )