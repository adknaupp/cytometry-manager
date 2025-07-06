from fastapi import APIRouter
from fastui.forms import SelectSearchResponse
from sqlmodel import select

from .models import Cohort, Project, Sample, Subject
from .database import SessionDep

router = APIRouter()

@router.get('/projects', response_model=SelectSearchResponse)
async def project_search_view(q: str = "", session: SessionDep = None) -> SelectSearchResponse:
    # Query projects by name, case-insensitive, partial match
    query = select(Project)
    if q:
        query = query.where(Project.name.ilike(f"%{q}%"))
    projects = session.exec(query).all()
    if not q:
        # If no query, return first 20 projects sorted by name
        projects = sorted(projects, key=lambda p: p.name)[:20]
    options = [{"value": str(p.id), "label": p.name} for p in projects]
    return SelectSearchResponse(options=options)

@router.get("/sample-types", response_model=SelectSearchResponse)
async def sample_type_search_view(q: str = "", session: SessionDep = None) -> SelectSearchResponse:
    # Query distinct sample types, case-insensitive, partial match
    query = select(Sample.type).distinct()
    if q:
        query = query.where(Sample.type.ilike(f"%{q}%"))
    sample_types = session.exec(query).all()
    # Flatten list if returned as list of tuples
    sample_types = [st[0] if isinstance(st, tuple) else st for st in sample_types]
    if not q and len(sample_types) > 20:
        # If no query, return first 20 sample types sorted
        sample_types = sorted(sample_types)[:20]
    options = [{"value": st, "label": st} for st in sample_types if st]
    return SelectSearchResponse(options=options)

@router.get("/subjects", response_model=SelectSearchResponse)
async def subject_search_view(q: str = "", session: SessionDep = None) -> SelectSearchResponse:
    # Query subjects by name, case-insensitive, partial match
    query = select(Subject)
    if q:
        query = query.where(Subject.name.ilike(f"%{q}%"))
    subjects = session.exec(query).all()
    # Flatten list if returned as list of tuples
    subjects = [s[0] if isinstance(s, tuple) else s for s in subjects]
    if not q and len(subjects) > 20:
        # If no query, return first 20 subjects sorted
        subjects = sorted(subjects, key=lambda s: s.name)[:20]
    options = [{"value": str(s.id), "label": s.name} for s in subjects]
    return SelectSearchResponse(options=options)

@router.get("/cohorts", response_model=SelectSearchResponse)
async def cohort_search_view(q: str = "", session: SessionDep = None) -> SelectSearchResponse:
    # Query cohorts by name, case-insensitive, partial match
    query = select(Cohort)
    if q:
        query = query.where(Cohort.name.ilike(f"%{q}%"))
    cohorts = session.exec(query).all()
    if not q:
        # If no query, return first 20 cohorts sorted by name
        cohorts = sorted(cohorts, key=lambda c: c.name)[:20]
    options = [{"value": str(c.id), "label": c.name} for c in cohorts]
    return SelectSearchResponse(options=options)
