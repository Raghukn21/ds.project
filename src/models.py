"""
Model Architecture Module for AgriGuard AI
Defines multi-label classification and severity estimation models
"""

import torch
import torch.nn as nn
import torchvision.models as models
from typing import Dict, List, Optional
import timm


class MultiLabelPlantClassifier(nn.Module):
    """
    Multi-label plant health classifier
    Predicts: diseases, pests, abiotic stresses simultaneously
    """
    
    def __init__(
        self,
        num_diseases: int = 7,
        num_pests: int = 5,
        num_abiotic: int = 5,
        backbone: str = 'efficientnet_b0',
        pretrained: bool = True,
        dropout: float = 0.3
    ):
        """
        Args:
            num_diseases: Number of disease classes
            num_pests: Number of pest classes
            num_abiotic: Number of abiotic stress classes
            backbone: Backbone architecture name
            pretrained: Whether to use pretrained weights
            dropout: Dropout rate
        """
        super(MultiLabelPlantClassifier, self).__init__()
        
        self.num_diseases = num_diseases
        self.num_pests = num_pests
        self.num_abiotic = num_abiotic
        self.num_labels = num_diseases + num_pests + num_abiotic
        
        # Load backbone
        if backbone.startswith('efficientnet'):
            self.backbone = getattr(models, backbone)(pretrained=pretrained)
            feature_dim = self.backbone.classifier[1].in_features
            self.backbone.classifier = nn.Identity()
        elif backbone.startswith('resnet'):
            self.backbone = getattr(models, backbone)(pretrained=pretrained)
            feature_dim = self.backbone.fc.in_features
            self.backbone.fc = nn.Identity()
        elif backbone.startswith('vit'):
            self.backbone = timm.create_model(backbone, pretrained=pretrained, num_classes=0)
            feature_dim = self.backbone.embed_dim
        else:
            raise ValueError(f"Unsupported backbone: {backbone}")
        
        # Shared layers
        self.shared_layers = nn.Sequential(
            nn.Linear(feature_dim, 512),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # Disease classification head
        self.disease_head = nn.Linear(256, num_diseases)
        
        # Pest classification head
        self.pest_head = nn.Linear(256, num_pests)
        
        # Abiotic stress classification head
        self.abiotic_head = nn.Linear(256, num_abiotic)
        
        # Health status head (healthy/stressed/diseased)
        self.health_head = nn.Linear(256, 3)
        
        # Severity estimation head (regression: 0-3)
        self.severity_head = nn.Linear(256, 1)
    
    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass
        
        Returns:
            Dictionary with predictions:
                - diseases: (B, num_diseases) logits
                - pests: (B, num_pests) logits
                - abiotic: (B, num_abiotic) logits
                - health_status: (B, 3) logits
                - severity: (B, 1) regression output
        """
        # Extract features
        features = self.backbone(x)
        shared = self.shared_layers(features)
        
        # Multi-label predictions
        disease_logits = self.disease_head(shared)
        pest_logits = self.pest_head(shared)
        abiotic_logits = self.abiotic_head(shared)
        
        # Health status and severity
        health_logits = self.health_head(shared)
        severity = torch.sigmoid(self.severity_head(shared)) * 3  # Scale to 0-3
        
        return {
            'diseases': disease_logits,
            'pests': pest_logits,
            'abiotic': abiotic_logits,
            'health_status': health_logits,
            'severity': severity.squeeze(-1)
        }


class SingleStageMultiLabelModel(nn.Module):
    """
    Simplified single-stage multi-label model
    All labels in one output layer
    """
    
    def __init__(
        self,
        num_labels: int = 17,
        backbone: str = 'efficientnet_b0',
        pretrained: bool = True,
        dropout: float = 0.3
    ):
        """
        Args:
            num_labels: Total number of labels (diseases + pests + abiotic)
            backbone: Backbone architecture
            pretrained: Use pretrained weights
            dropout: Dropout rate
        """
        super(SingleStageMultiLabelModel, self).__init__()
        
        # Load backbone
        if backbone.startswith('efficientnet'):
            self.backbone = getattr(models, backbone)(pretrained=pretrained)
            feature_dim = self.backbone.classifier[1].in_features
            self.backbone.classifier = nn.Identity()
        elif backbone.startswith('resnet'):
            self.backbone = getattr(models, backbone)(pretrained=pretrained)
            feature_dim = self.backbone.fc.in_features
            self.backbone.fc = nn.Identity()
        else:
            raise ValueError(f"Unsupported backbone: {backbone}")
        
        # Classification layers
        self.classifier = nn.Sequential(
            nn.Linear(feature_dim, 512),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, num_labels)
        )
        
        # Separate heads for health status and severity
        self.health_head = nn.Linear(256, 3)
        self.severity_head = nn.Linear(256, 1)
    
    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass"""
        features = self.backbone(x)
        shared = self.classifier[:-2](features)  # Get features before final layer
        
        # Multi-label predictions
        multi_label_logits = self.classifier(shared)
        
        # Health status and severity
        health_logits = self.health_head(shared)
        severity = torch.sigmoid(self.severity_head(shared)) * 3
        
        return {
            'multi_label': multi_label_logits,
            'health_status': health_logits,
            'severity': severity.squeeze(-1)
        }


class TwoStageModel(nn.Module):
    """
    Two-stage model combining detection and classification
    """
    
    def __init__(
        self,
        detector: Optional[nn.Module] = None,
        classifier: Optional[nn.Module] = None
    ):
        """
        Args:
            detector: Plant detection model (YOLO-based)
            classifier: Multi-label classification model
        """
        super(TwoStageModel, self).__init__()
        self.detector = detector
        self.classifier = classifier
    
    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass through both stages
        Note: In practice, detection and classification are often done separately
        """
        # Stage 1: Detection (if detector is provided)
        if self.detector is not None:
            # This would typically be done with raw images
            # For now, pass through
            pass
        
        # Stage 2: Classification
        if self.classifier is not None:
            return self.classifier(x)
        
        return {}


class SeverityEstimationModel(nn.Module):
    """
    Dedicated model for severity estimation
    Can be used standalone or as part of multi-task model
    """
    
    def __init__(
        self,
        backbone: str = 'efficientnet_b0',
        pretrained: bool = True,
        num_severity_levels: int = 4  # 0, 1, 2, 3
    ):
        """
        Args:
            backbone: Backbone architecture
            pretrained: Use pretrained weights
            num_severity_levels: Number of severity levels
        """
        super(SeverityEstimationModel, self).__init__()
        
        # Load backbone
        if backbone.startswith('efficientnet'):
            self.backbone = getattr(models, backbone)(pretrained=pretrained)
            feature_dim = self.backbone.classifier[1].in_features
            self.backbone.classifier = nn.Identity()
        elif backbone.startswith('resnet'):
            self.backbone = getattr(models, backbone)(pretrained=pretrained)
            feature_dim = self.backbone.fc.in_features
            self.backbone.fc = nn.Identity()
        else:
            raise ValueError(f"Unsupported backbone: {backbone}")
        
        # Regression head
        self.regression_head = nn.Sequential(
            nn.Linear(feature_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 1)
        )
        
        # Classification head (alternative)
        self.classification_head = nn.Sequential(
            nn.Linear(feature_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_severity_levels)
        )
    
    def forward(self, x: torch.Tensor, mode: str = 'regression') -> torch.Tensor:
        """
        Forward pass
        
        Args:
            x: Input tensor
            mode: 'regression' or 'classification'
        
        Returns:
            Severity prediction
        """
        features = self.backbone(x)
        
        if mode == 'regression':
            severity = torch.sigmoid(self.regression_head(features)) * 3
            return severity.squeeze(-1)
        else:
            return self.classification_head(features)


def get_model(
    model_type: str = 'multi_label',
    backbone: str = 'efficientnet_b0',
    **kwargs
) -> nn.Module:
    """
    Factory function to get model by type
    
    Args:
        model_type: Type of model ('multi_label', 'single_stage', 'severity')
        backbone: Backbone architecture
        **kwargs: Additional arguments for model initialization
    
    Returns:
        Model instance
    """
    if model_type == 'multi_label':
        return MultiLabelPlantClassifier(backbone=backbone, **kwargs)
    elif model_type == 'single_stage':
        return SingleStageMultiLabelModel(backbone=backbone, **kwargs)
    elif model_type == 'severity':
        return SeverityEstimationModel(backbone=backbone, **kwargs)
    else:
        raise ValueError(f"Unknown model type: {model_type}")


if __name__ == "__main__":
    # Test model creation
    model = get_model('multi_label', backbone='efficientnet_b0')
    print(f"Model created with {sum(p.numel() for p in model.parameters())} parameters")
    
    # Test forward pass
    x = torch.randn(2, 3, 224, 224)
    outputs = model(x)
    print(f"Output keys: {outputs.keys()}")
    for key, val in outputs.items():
        print(f"{key}: {val.shape}")
