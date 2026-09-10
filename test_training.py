"""
Test training module with sample data
"""

from src.train import train_model
from src.data_loader import get_data_loaders
import torch

print("Testing training pipeline...")

try:
    # Get data loaders
    print("Loading data...")
    data_loaders = get_data_loaders(
        data_dir='data/raw',
        metadata_file='data/raw/metadata.csv',
        batch_size=4,
        num_workers=0,
        image_size=224
    )
    print("✓ Data loaded successfully")
    
    # Test a quick training run (1 epoch)
    print("\nStarting quick training test (1 epoch)...")
    model = train_model(
        data_dir='data/raw',
        metadata_file='data/raw/metadata.csv',
        model_type='multi_label',
        backbone='efficientnet_b0',
        num_epochs=1,
        batch_size=4,
        learning_rate=1e-4,
        device='cpu',  # Use CPU for testing
        num_workers=0
    )
    
    print("✓ Training test passed!")
    
except Exception as e:
    print(f"✗ Training test failed: {e}")
    import traceback
    traceback.print_exc()
