"""
AgriGuard AI - Full-Plant Health Assessment System
"""

__version__ = "1.0.0"
__author__ = "AgriGuard AI Team"

# Import key modules for easier access
from .models import get_model
from .data_loader import get_data_loaders, FullPlantDataset
from .train import train_model, Trainer
from .inference import PlantHealthInference
from .advisory import AdvisoryEngine
from .evaluate import MultiLabelEvaluator
