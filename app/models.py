from typing import Literal, Sequence
from sqlmodel import SQLModel, Relationship
import pydantic
import sqlmodel
from enum import Enum

class SexEnum(str, Enum):
    MALE = 'M'
    FEMALE = 'F'
    ANY = 'Any'

class ResponseEnum(str, Enum):
    YES = 'yes'
    NO = 'no'
    ANY = 'Any'

class TreatmentEnum(str, Enum):
    MIRACLIB = 'miraclib'
    PHAUXIMAB = 'phauximab'
    ANY = 'Any'

class Project(SQLModel, table=True):
    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    name: str
    num_samples: int = sqlmodel.Field(default=0)
    samples: list["Sample"] = Relationship(back_populates="project")

class Subject(SQLModel, table=True):
    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    name: str
    # project_id: int = Field(foreign_key="project.id") # project can't(?) back_populate both subject and sample
    condition: str
    age: int
    sex: SexEnum
    treatment: str
    response: ResponseEnum | None = None
    samples: list["Sample"] = Relationship(back_populates="subject")

class Sample(SQLModel, table=True):
    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    name: str
    subject_id: int | None = sqlmodel.Field(foreign_key="subject.id")
    project_id: int | None = sqlmodel.Field(foreign_key="project.id")
    type: str
    time_from_treatment_start: int
    b_cell: int
    cd8_t_cell: int
    cd4_t_cell: int
    nk_cell: int
    monocyte: int
    subject: Subject | None = Relationship(back_populates="samples")
    project: Project | None = Relationship(back_populates="samples")

    def get_population_frequencies(self) -> dict[str, float]:
        """Calculate the relative frequencies of immune cell populations in this sample."""
        total_cells = self.b_cell + self.cd8_t_cell + self.cd4_t_cell + self.nk_cell + self.monocyte
        if total_cells == 0:
            return {
                "B Cell": 0.0,
                "CD8 T Cell": 0.0,
                "CD4 T Cell": 0.0,
                "NK Cell": 0.0,
                "Monocyte": 0.0
            }
        return {
            "B Cell": (self.b_cell / total_cells) * 100,
            "CD8 T Cell": (self.cd8_t_cell / total_cells) * 100,
            "CD4 T Cell": (self.cd4_t_cell / total_cells) * 100,
            "NK Cell": (self.nk_cell / total_cells) * 100,
            "Monocyte": (self.monocyte / total_cells) * 100
        }

class Cohort(SQLModel, table=True):
    '''
    A collection of qualifiers for dynamically defining a set of subjects.
    In other words, a set of criteria for selecting subjects in the database.
    '''
    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    name: str
    condition: str | None = sqlmodel.Field(default='Any')
    sex: SexEnum | None = sqlmodel.Field(default=SexEnum.ANY)
    treatment: TreatmentEnum | None = sqlmodel.Field(default=TreatmentEnum.ANY)
    # response: ResponseEnum | None = sqlmodel.Field(default=ResponseEnum.ANY)
    datasets: list["Dataset"] = Relationship(back_populates="cohort")

    def get_subjects(self, session: sqlmodel.Session) -> Sequence[Subject]:
        query = sqlmodel.select(Subject)
        if self.condition and self.condition != 'Any':
            query = query.where(Subject.condition == self.condition)
        if self.sex and self.sex != SexEnum.ANY:
            query = query.where(Subject.sex == self.sex)
        if self.treatment and self.treatment != TreatmentEnum.ANY:
            query = query.where(Subject.treatment == self.treatment)
        #if self.response and self.response != ResponseEnum.ANY:
        #    query = query.where(Subject.response == self.response)
        return session.exec(query).all()

class Dataset(SQLModel, table=True):
    '''
    A collection of qualifiers for dynamically defining a set of samples.
    In other words, a set of filters for selecting samples using a
    given cohort and other criteria.
    '''
    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    name: str
    cohort_id: int = sqlmodel.Field(foreign_key="cohort.id")
    cohort: Cohort | None = Relationship(back_populates="datasets")
    sample_type: str
    time_from_treatment_start: int

    def get_samples(self, session: sqlmodel.Session) -> Sequence[Sample]:
        query = sqlmodel.select(Sample)
        cohort = session.get(Cohort, self.cohort_id)
        if cohort:
            dataset_subjects = cohort.get_subjects(session)
            subject_ids = [subject.id for subject in dataset_subjects]
            query = query.where(Sample.subject_id.in_(subject_ids))
        if self.sample_type:
            query = query.where(Sample.type == self.sample_type)
        if self.time_from_treatment_start:
            query = query.where(Sample.time_from_treatment_start == self.time_from_treatment_start)
        return session.exec(query).all()


# NOTE: use Literal here instead of enums from models.py to allow for JSON schema 'placeholder' to take effect
ResponseType = Literal['yes', 'no']
TreatmentType = Literal['miraclib', 'phauximab'] # TODO: should be dynamic later
SexType = Literal['M', 'F']
SampleType = Literal['PBMC', 'WB'] # TODO: should be dynamic later

class SubjectFilterForm(pydantic.BaseModel):
    sex: SexType | None = pydantic.Field(json_schema_extra={'placeholder': 'Filter by Sex...'})
    response: ResponseType | None = pydantic.Field(json_schema_extra={'placeholder': 'Filter by Response...'})
    treatment: TreatmentType | None = pydantic.Field(json_schema_extra={'placeholder': 'Filter by Treatment...'})
    name: str | None = pydantic.Field(json_schema_extra={'placeholder': 'Filter by Name...'})

class DatasetSampleFilterForm(pydantic.BaseModel):
    # name: str | None = pydantic.Field(json_schema_extra={'placeholder': 'Filter by Name...'})
    sex: SexType | None = pydantic.Field(json_schema_extra={'placeholder': 'Filter by Sex...'})
    response: ResponseType | None = pydantic.Field(json_schema_extra={'placeholder': 'Filter by Response...'})

class SampleForm(SQLModel, table=False):
    project_id: str = pydantic.Field(title="Project", json_schema_extra={"search_url": "/api/search/projects"})
    subject_id: str = pydantic.Field(title="Subject", json_schema_extra={"search_url": "/api/search/subjects"})
    name: str
    type: str
    time_from_treatment_start: int
    b_cell: int
    cd8_t_cell: int
    cd4_t_cell: int
    nk_cell: int
    monocyte: int

class SubjectForm(pydantic.BaseModel):
    name: str
    condition: str
    age: int
    sex: SexType
    treatment: str | None = None
    response: ResponseType | None = None

class CohortForm(pydantic.BaseModel):
    name: str
    condition: str | None = pydantic.Field(default=None, json_schema_extra={"placeholder": "Any"})
    sex: SexType | None = pydantic.Field(default=None, json_schema_extra={"placeholder": "Any"})
    treatment: TreatmentType | None = pydantic.Field(default=None, json_schema_extra={"placeholder": "Any"})
    # response: str | None = pydantic.Field(default=None, json_schema_extra={"placeholder": "Any"})

class DatasetForm(pydantic.BaseModel):
    name: str
    cohort_id: str = pydantic.Field(title="Cohort", json_schema_extra={"search_url": "/api/search/cohorts"})
    sample_type: SampleType
    time_from_treatment_start: int