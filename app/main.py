from fastapi import APIRouter
from fastui import AnyComponent, FastUI
from fastui import components as c

from .shared import base_page

router = APIRouter()

@router.get("/", response_model=FastUI, response_model_exclude_none=True)
def api_index() -> list[AnyComponent]:
    return base_page(
        c.Heading(text='Cytometry Manager', level=2),
        c.Paragraph(text='Welcome to the Cytometry Manager! Choose a page in the navigation bar to get started.'),
    )

@router.get("/help/", response_model=FastUI, response_model_exclude_none=True)
def help_page() -> list[AnyComponent]:
    return base_page(
        c.Markdown(
            text="""\
# Help

## Projects, Samples and Subjects

Samples, projects and subjects are basic entities since they are imported straight from CSV datasets.
Cell count data belongs to samples, making them most important for analysis.
However, facts such as the treatment response associated with the sample are also important.
Treatment response is a variable belonging to a subject, so each sample has an associated subject so that this and other variables are available when choosing data to analyze.
See the table headers on the Sample and Subject pages to see what other variables exist and which values are present.
Links are provided in table entries to make it easy to examine related data.

#### Add/remove samples

To manually enter a new sample, visit the Samples page and click "New Sample".
To remove a sample, click the link in the table entry to see the sample details.
A delete button is available at the bottom.

#### Add/remove/modify subjects and projects

Yet to be implemented...

## Cohorts and Datasets

Cohorts and Datasets are fundamentally different than the basic entities.
Essentially, a cohort defines a group of subjects and a dataset defines a group of samples.
This is achieved by storing the intended characteristics of the subjects or samples belonging to a cohort or a dataset, respectively.
Thus, the subjects or samples belonging to the cohort may actually change if new samples or subjects are added, depending on the characteristics of said subjects or samples.

## Analyzing differences in response across cell types

Treatment groups may vary in cell type frequency that correlates with a response to the treatment.
To examine whether a treatment group exhibits this variation, the first step is to define a cohort.

#### Create a cohort
For example, we can create a cohort of subjects that have melanoma and have be treated with miraclib.
Visit the Subjects page, and click "New Cohort".
Enter a name for this cohort, select "miraclib", and hit submit.

#### Create a dataset
Next, we can use our cohort to create a dataset for analysis.
Visit the Cohorts page and select your new cohort by clicking the link in the cohort name.
This will open a page of information about this cohort.
Under "Samples", we see all the samples that are associated with a subject in our cohort.
This group of samples may be just right for some analyses, but in our case, we only want PBMC samples.
Creating a dataset will allow us to further refine a group of samples to analyze based on sample characteristics (e.g., time from treatment start, sample type, etc.)
If you don't need to exclude any samples found in a cohort, you can create a dataset with merely a name and the cohort.
Either way, to continue with analysis, we need to create a dataset.

A new dataset can be created from the samples section of a given cohort page.
Click the "New Cohort" button and enter choose any applicable filters.
For example, Sample Type of PBMC, your cohort name, and time from treatment start of 0.

#### Visualize cell type frequencies and response
Creating a cohort and a dataset has effectively gathered the set of samples that are appropriate for our analysis.
Now, we can visualize the cell type frequency data found in those samples.
Visit the Datasets page a click on the link the dataset we just created.
This will bring details about our dataset.
Click on "Visualizations" to generate a plot of cell type frequencies given the response (yes or no).
We can also view the samples in our dataset to make sure meet our expectations.
"""
        )
    )