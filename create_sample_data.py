"""
Create sample data and metadata for testing AgriGuard AI
"""

import pandas as pd
import numpy as np
from PIL import Image
import os

# Create directories
os.makedirs('data/raw/full_plant_images', exist_ok=True)

# Define sample data
np.random.seed(42)

# Generate 30 sample images with different characteristics
sample_data = []
crop_types = ['tomato', 'chili', 'cotton', 'potato', 'rice', 'wheat', 'maize']
growth_stages = ['vegetative', 'flowering', 'fruiting']
health_statuses = ['healthy', 'stressed', 'diseased']

disease_labels = ['early_blight', 'late_blight', 'powdery_mildew', 'leaf_spot', 
                  'bacterial_spot', 'viral_infection', 'fungal_infection']
pest_labels = ['aphids', 'whiteflies', 'thrips', 'spider_mites', 'caterpillars']
abiotic_labels = ['nutrient_deficiency', 'water_stress', 'heat_stress', 
                  'salt_stress', 'light_stress']

for i in range(1, 31):
    # Randomly assign attributes
    crop_type = np.random.choice(crop_types)
    growth_stage = np.random.choice(growth_stages)
    health_status = np.random.choice(health_statuses, p=[0.4, 0.3, 0.3])
    
    # Assign severity based on health status
    if health_status == 'healthy':
        severity = 0
    elif health_status == 'stressed':
        severity = np.random.choice([1, 2])
    else:  # diseased
        severity = np.random.choice([1, 2, 3], p=[0.3, 0.5, 0.2])
    
    # Create image with different colors based on health
    if health_status == 'healthy':
        color = (34, 139, 34)  # Green
    elif health_status == 'stressed':
        color = (154, 205, 50)  # Yellow-green
    else:  # diseased
        color = (139, 69, 19)  # Brown
    
    img = Image.new('RGB', (224, 224), color=color)
    img_path = f'full_plant_images/img_{i:03d}.jpg'
    img.save(f'data/raw/{img_path}')
    
    # Create row data
    row = {
        'image_id': f'img_{i:03d}',
        'image_path': img_path,
        'split': np.random.choice(['train', 'train', 'train', 'val', 'test']),
        'crop_type': crop_type,
        'growth_stage': growth_stage,
        'health_status': health_status,
        'severity': severity
    }
    
    # Add disease labels (randomly, more likely if diseased)
    for disease in disease_labels:
        if health_status == 'diseased':
            row[disease] = 1 if np.random.random() < 0.3 else 0
        else:
            row[disease] = 0
    
    # Add pest labels (randomly)
    for pest in pest_labels:
        row[pest] = 1 if np.random.random() < 0.15 else 0
    
    # Add abiotic labels (more likely if stressed)
    for abiotic in abiotic_labels:
        if health_status == 'stressed':
            row[abiotic] = 1 if np.random.random() < 0.4 else 0
        else:
            row[abiotic] = 1 if np.random.random() < 0.1 else 0
    
    sample_data.append(row)

# Create DataFrame and save
df = pd.DataFrame(sample_data)
df.to_csv('data/raw/metadata.csv', index=False)
print(f"Created metadata with {len(df)} samples")
print(f"Split distribution: {df['split'].value_counts().to_dict()}")
print(f"Health status distribution: {df['health_status'].value_counts().to_dict()}")
print(f"Sample data saved to data/raw/metadata.csv")
