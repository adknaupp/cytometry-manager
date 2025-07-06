import os
import csv
from typing import Annotated

from fastapi import Depends
from sqlmodel import SQLModel, Session, create_engine, select
import pandas as pd

from app.models import Dataset, DatasetForm, Project, Subject, Sample, SampleForm, SubjectForm, Cohort, CohortForm

DB_FILE = 'db.sqlite3'
CSV_FILE = 'cell-count.csv'
engine = create_engine(f'sqlite:///{DB_FILE}')

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

def init_db():
    SQLModel.metadata.create_all(engine)

def load_csv():
    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(f"{CSV_FILE} not found.")

    projects = {}
    subjects = {}
    samples = []
    project_sample_counts = {}

    with open(CSV_FILE, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Project
            project_name = row['project']
            if project_name not in projects:
                projects[project_name] = Project(name=project_name, num_samples=0)
                project_sample_counts[project_name] = 0
            project_sample_counts[project_name] += 1
            # Subject (unique by subject name)
            subject_key = row['subject']
            if subject_key not in subjects:
                subjects[subject_key] = Subject(
                    name=row['subject'],
                    condition=row['condition'],
                    age=int(row['age']),
                    sex=row['sex'],
                    treatment=row['treatment'],
                    response=row['response'] if row['response'] else None
                )
            # Sample (store for later, after IDs are assigned)
            samples.append(row)

    with Session(engine) as session:
        # Insert projects and set num_samples
        for project_name, project in projects.items():
            project.num_samples = project_sample_counts[project_name]
            session.add(project)
        session.commit()
        # Refresh to get IDs
        for project in projects.values():
            session.refresh(project)
        # Insert subjects
        for subject in subjects.values():
            session.add(subject)
        session.commit()
        for subject in subjects.values():
            session.refresh(subject)
        # Map for quick lookup
        project_id_map = {p.name: p.id for p in projects.values()}
        subject_id_map = {s.name: s.id for s in subjects.values()}
        # Insert samples
        for row in samples:
            sample = Sample(
                name=row['sample'],
                subject_id=subject_id_map[row['subject']],
                project_id=project_id_map[row['project']],
                type=row['sample_type'],
                time_from_treatment_start=int(row['time_from_treatment_start']),
                b_cell=int(row['b_cell']),
                cd8_t_cell=int(row['cd8_t_cell']),
                cd4_t_cell=int(row['cd4_t_cell']),
                nk_cell=int(row['nk_cell']),
                monocyte=int(row['monocyte'])
            )
            session.add(sample)
        session.commit()


def add_sample(form: SampleForm, session: Session):
    '''
    Assuming that subject and project IDs are correct since 
    the options in the form are populated from the database.
    '''
    sample = Sample(
        name=form.name,
        subject_id=form.subject_id,
        project_id=form.project_id,
        type=form.type,
        time_from_treatment_start=form.time_from_treatment_start,
        b_cell=form.b_cell,
        cd8_t_cell=form.cd8_t_cell,
        cd4_t_cell=form.cd4_t_cell,
        nk_cell=form.nk_cell,
        monocyte=form.monocyte
    )
    session.add(sample)
    session.commit()

def add_subject(form: SubjectForm, session: Session):
    subject = Subject(
        name=form.name,
        condition=form.condition,
        age=form.age,
        sex=form.sex,
        treatment=form.treatment,
        response=form.response
    )
    session.add(subject)
    session.commit()

def add_cohort(form: CohortForm, session: Session):
    cohort = Cohort(
        name=form.name,
        condition=form.condition,
        sex=form.sex,
        treatment=form.treatment,
    )
    session.add(cohort)
    session.commit()

def add_dataset(form: DatasetForm, session: Session):
    dataset = Dataset(
        name=form.name,
        cohort_id=form.cohort_id,
        sample_type=form.sample_type,
        time_from_treatment_start=form.time_from_treatment_start
    )
    session.add(dataset)
    session.commit()

if __name__ == '__main__':
    init_db()
    load_csv()
    print('Database initialized and CSV loaded.')
