from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

from app.database import SessionDep
from app.models import Dataset, Subject

router = APIRouter()

@router.get("/dataset/{id}")
def get_dataset_visualization(id: int, session: SessionDep):
    dataset = session.get(Dataset, id)
    if not dataset:
        # Return a simple error image or raise an HTTP exception
        raise HTTPException(status_code=404, detail=f"Dataset {id} not found")
    
    samples = dataset.get_samples(session)
    
    rows_data = []
    for samp in samples:
        populations = samp.get_population_frequencies()
        subject = session.get(Subject, samp.subject_id)
        response = None
        if subject:
            response = subject.response
        if response:
            rows_data.append({
                'B Cell': populations['B Cell'],
                'Cd8 T Cell': populations['CD8 T Cell'],
                'Cd4 T Cell': populations['CD4 T Cell'],
                'Nk Cell': populations['NK Cell'],
                'Monocyte': populations['Monocyte'],
                'Response': response.value if response else None
            })
    
    data_points = pd.DataFrame(rows_data)
    
    if data_points.empty:
        raise HTTPException(status_code=404, detail="No data available for visualization")
    
    # Melt the dataframe for seaborn - convert from wide to long format
    cell_types = ['B Cell', 'Cd8 T Cell', 'Cd4 T Cell', 'Nk Cell', 'Monocyte']
    melted_df = pd.melt(data_points, id_vars=['Response'], value_vars=cell_types, 
                       var_name='Cell_Type', value_name='Frequency')
    
    # Set the style for better-looking plots
    sns.set_style("whitegrid")
    plt.rcParams['figure.facecolor'] = 'white'
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Create boxplot with seaborn
    sns.boxplot(data=melted_df, x='Cell_Type', y='Frequency', hue='Response', ax=ax)
    
    # Customize the plot
    ax.set_title(f'Cell Population Frequencies by Response - Dataset "{dataset.name}"', fontsize=12, fontweight='bold')
    ax.set_xlabel('Cell Type', fontsize=10)
    ax.set_ylabel('Frequency (%)', fontsize=10)
    ax.legend(title='Response', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right', fontsize=9)
    plt.yticks(fontsize=9)
    
    # Adjust layout to prevent clipping
    plt.tight_layout()
    
    # Save plot to bytes
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
    img_buffer.seek(0)
    
    # Close the figure to free memory
    plt.close(fig)
    
    return StreamingResponse(
        img_buffer,
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename=dataset_{id}_visualization.png"}
    )