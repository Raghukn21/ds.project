"""
Test data loader module
"""

from src.data_loader import get_data_loaders
import torch

print("Testing data loader...")

try:
    # Get data loaders
    data_loaders = get_data_loaders(
        data_dir='data/raw',
        metadata_file='data/raw/metadata.csv',
        batch_size=4,
        num_workers=0,  # Use 0 for Windows compatibility
        image_size=224
    )
    
    print("✓ Data loaders created successfully")
    
    # Test loading a batch
    for split, loader in data_loaders.items():
        print(f"\nTesting {split} split...")
        images, labels = next(iter(loader))
        print(f"  Batch shape: {images.shape}")
        print(f"  Labels keys: {labels.keys()}")
        print(f"  Multi-label shape: {labels['multi_label'].shape}")
        print(f"  Severity shape: {labels['severity'].shape}")
        print(f"  Health status shape: {labels['health_status'].shape}")
        print(f"  ✓ {split} split working")
    
    print("\n✓ Data loader test passed!")
    
except Exception as e:
    print(f"✗ Data loader test failed: {e}")
    import traceback
    traceback.print_exc()
