"""
Data Loader Module for AgriGuard AI
Handles loading and preprocessing of full-plant image datasets
"""

import os
import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
import numpy as np
from typing import Dict, List, Tuple, Optional


class FullPlantDataset(Dataset):
    """Dataset class for full-plant images with multi-label annotations"""
    
    def __init__(
        self,
        data_dir: str,
        metadata_file: str,
        transform: Optional[transforms.Compose] = None,
        split: str = 'train'
    ):
        """
        Args:
            data_dir: Directory containing images
            metadata_file: Path to CSV file with annotations
            transform: Optional transform to be applied on images
            split: One of 'train', 'val', or 'test'
        """
        self.data_dir = data_dir
        self.transform = transform
        
        # Load metadata
        self.metadata = pd.read_csv(metadata_file)
        
        # Filter by split if specified
        if 'split' in self.metadata.columns:
            self.metadata = self.metadata[self.metadata['split'] == split]
        
        # Define label columns
        self.label_columns = [
            col for col in self.metadata.columns 
            if col not in ['image_id', 'image_path', 'split', 'crop_type', 
                          'growth_stage', 'severity', 'health_status']
        ]
        
        # Define all possible labels for multi-label classification
        self.disease_labels = [
            'early_blight', 'late_blight', 'powdery_mildew', 'leaf_spot',
            'bacterial_spot', 'viral_infection', 'fungal_infection'
        ]
        self.pest_labels = [
            'aphids', 'whiteflies', 'thrips', 'spider_mites', 'caterpillars'
        ]
        self.abiotic_labels = [
            'nutrient_deficiency', 'water_stress', 'heat_stress', 
            'salt_stress', 'light_stress'
        ]
        self.all_labels = self.disease_labels + self.pest_labels + self.abiotic_labels
        
    def __len__(self) -> int:
        return len(self.metadata)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, Dict]:
        """
        Returns:
            image: Tensor image
            labels: Dictionary containing:
                - multi_label: Multi-label binary vector
                - severity: Severity score (0-3)
                - health_status: Health status label
                - crop_type: Crop type
        """
        # Get image path
        img_path = os.path.join(self.data_dir, self.metadata.iloc[idx]['image_path'])
        
        # Load image
        image = Image.open(img_path).convert('RGB')
        
        # Apply transforms
        if self.transform:
            image = self.transform(image)
        
        # Get labels
        row = self.metadata.iloc[idx]
        
        # Multi-label vector
        multi_label = torch.zeros(len(self.all_labels), dtype=torch.float32)
        for i, label in enumerate(self.all_labels):
            if label in self.label_columns and row.get(label, 0) == 1:
                multi_label[i] = 1.0
        
        # Severity
        severity = row.get('severity', 0)
        
        # Health status
        health_status_map = {'healthy': 0, 'stressed': 1, 'diseased': 2}
        health_status = health_status_map.get(row.get('health_status', 'healthy'), 0)
        
        labels = {
            'multi_label': multi_label,
            'severity': torch.tensor(severity, dtype=torch.float32),
            'health_status': torch.tensor(health_status, dtype=torch.long),
            'crop_type': row.get('crop_type', 'unknown')
        }
        
        return image, labels


def get_data_loaders(
    data_dir: str,
    metadata_file: str,
    batch_size: int = 32,
    num_workers: int = 4,
    image_size: int = 224
) -> Dict[str, DataLoader]:
    """
    Create train, validation, and test data loaders
    
    Args:
        data_dir: Directory containing images
        metadata_file: Path to metadata CSV
        batch_size: Batch size for data loaders
        num_workers: Number of worker processes
        image_size: Target image size for resizing
    
    Returns:
        Dictionary with 'train', 'val', 'test' DataLoaders
    """
    # Define transforms
    train_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Create datasets
    train_dataset = FullPlantDataset(data_dir, metadata_file, train_transform, 'train')
    val_dataset = FullPlantDataset(data_dir, metadata_file, val_transform, 'val')
    test_dataset = FullPlantDataset(data_dir, metadata_file, val_transform, 'test')
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, 
        num_workers=num_workers, pin_memory=True
    )
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=True
    )
    test_loader = DataLoader(
        test_dataset, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=True
    )
    
    return {
        'train': train_loader,
        'val': val_loader,
        'test': test_loader
    }


def create_sample_metadata(output_path: str):
    """Create a sample metadata CSV file for reference"""
    sample_data = {
        'image_id': ['img_001', 'img_002', 'img_003'],
        'image_path': ['full_plant_images/img_001.jpg', 'full_plant_images/img_002.jpg', 'full_plant_images/img_003.jpg'],
        'split': ['train', 'train', 'val'],
        'crop_type': ['tomato', 'tomato', 'chili'],
        'growth_stage': ['flowering', 'vegetative', 'fruiting'],
        'health_status': ['diseased', 'healthy', 'stressed'],
        'severity': [2, 0, 1],
        'early_blight': [1, 0, 0],
        'late_blight': [0, 0, 0],
        'powdery_mildew': [0, 0, 0],
        'leaf_spot': [0, 0, 1],
        'aphids': [0, 0, 1],
        'nutrient_deficiency': [0, 0, 1]
    }
    
    df = pd.DataFrame(sample_data)
    df.to_csv(output_path, index=False)
    print(f"Sample metadata created at {output_path}")


if __name__ == "__main__":
    # Create sample metadata
    create_sample_metadata("data/raw/metadata.csv")
