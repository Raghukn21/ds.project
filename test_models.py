"""
Test models module
"""

from src.models import get_model
import torch

print("Testing models...")

try:
    # Test multi-label model with EfficientNet backbone
    print("\nTesting multi-label model with EfficientNet-B0...")
    model = get_model(
        model_type='multi_label',
        backbone='efficientnet_b0',
        num_diseases=7,
        num_pests=5,
        num_abiotic=5,
        dropout=0.3
    )
    
    # Test forward pass
    dummy_input = torch.randn(2, 3, 224, 224)
    outputs = model(dummy_input)
    
    print(f"  Input shape: {dummy_input.shape}")
    print(f"  Output keys: {outputs.keys()}")
    print(f"  Disease logits shape: {outputs['diseases'].shape}")
    print(f"  Pest logits shape: {outputs['pests'].shape}")
    print(f"  Abiotic logits shape: {outputs['abiotic'].shape}")
    print(f"  Health status shape: {outputs['health_status'].shape}")
    print(f"  Severity shape: {outputs['severity'].shape}")
    print("  ✓ Multi-label model working")
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Total parameters: {total_params:,}")
    print(f"  Trainable parameters: {trainable_params:,}")
    
    print("\n✓ Models test passed!")
    
except Exception as e:
    print(f"✗ Models test failed: {e}")
    import traceback
    traceback.print_exc()
