"""
Evaluation Module for AgriGuard AI
Handles model evaluation with multi-label metrics
"""

import torch
import torch.nn as nn
import numpy as np
from sklearn.metrics import (
    precision_score, recall_score, f1_score, 
    accuracy_score, hamming_loss, mean_absolute_error, mean_squared_error
)
from typing import Dict, List, Tuple
from tqdm import tqdm


class MultiLabelEvaluator:
    """Evaluator for multi-label classification models"""
    
    def __init__(self, model: nn.Module, device: str = 'cuda'):
        """
        Args:
            model: Model to evaluate
            device: Device to run evaluation on
        """
        self.model = model.to(device)
        self.device = device
        self.model.eval()
    
    def evaluate(self, data_loader, threshold: float = 0.5) -> Dict[str, float]:
        """
        Evaluate model on dataset
        
        Args:
            data_loader: Data loader for evaluation
            threshold: Threshold for binary predictions
        
        Returns:
            Dictionary of metrics
        """
        all_predictions = []
        all_labels = []
        all_health_pred = []
        all_health_labels = []
        all_severity_pred = []
        all_severity_labels = []
        
        with torch.no_grad():
            for images, labels in tqdm(data_loader, desc="Evaluating"):
                images = images.to(self.device)
                
                # Get predictions
                outputs = self.model(images)
                
                # Multi-label predictions
                if 'multi_label' in outputs:
                    multi_label_pred = torch.sigmoid(outputs['multi_label']).cpu().numpy()
                    multi_label_true = labels['multi_label'].numpy()
                elif 'diseases' in outputs:
                    # Combine multi-head outputs
                    disease_pred = torch.sigmoid(outputs['diseases']).cpu().numpy()
                    pest_pred = torch.sigmoid(outputs['pests']).cpu().numpy()
                    abiotic_pred = torch.sigmoid(outputs['abiotic']).cpu().numpy()
                    multi_label_pred = np.concatenate([disease_pred, pest_pred, abiotic_pred], axis=1)
                    multi_label_true = labels['multi_label'].numpy()
                else:
                    continue
                
                # Health status predictions
                health_pred = torch.argmax(outputs['health_status'], dim=1).cpu().numpy()
                health_true = labels['health_status'].numpy()
                
                # Severity predictions
                severity_pred = outputs['severity'].cpu().numpy()
                severity_true = labels['severity'].numpy()
                
                all_predictions.append(multi_label_pred)
                all_labels.append(multi_label_true)
                all_health_pred.append(health_pred)
                all_health_labels.append(health_true)
                all_severity_pred.append(severity_pred)
                all_severity_labels.append(severity_true)
        
        # Concatenate all batches
        all_predictions = np.vstack(all_predictions)
        all_labels = np.vstack(all_labels)
        all_health_pred = np.concatenate(all_health_pred)
        all_health_labels = np.concatenate(all_health_labels)
        all_severity_pred = np.concatenate(all_severity_pred)
        all_severity_labels = np.concatenate(all_severity_labels)
        
        # Binary predictions
        binary_predictions = (all_predictions >= threshold).astype(int)
        
        # Calculate multi-label metrics
        metrics = {
            # Per-label metrics
            'precision_macro': precision_score(all_labels, binary_predictions, average='macro', zero_division=0),
            'recall_macro': recall_score(all_labels, binary_predictions, average='macro', zero_division=0),
            'f1_macro': f1_score(all_labels, binary_predictions, average='macro', zero_division=0),
            'precision_micro': precision_score(all_labels, binary_predictions, average='micro', zero_division=0),
            'recall_micro': recall_score(all_labels, binary_predictions, average='micro', zero_division=0),
            'f1_micro': f1_score(all_labels, binary_predictions, average='micro', zero_division=0),
            'hamming_loss': hamming_loss(all_labels, binary_predictions),
            
            # Health status metrics
            'health_accuracy': accuracy_score(all_health_labels, all_health_pred),
            
            # Severity metrics
            'severity_mae': mean_absolute_error(all_severity_labels, all_severity_pred),
            'severity_rmse': np.sqrt(mean_squared_error(all_severity_labels, all_severity_pred))
        }
        
        # Per-label F1 scores
        label_names = [
            'early_blight', 'late_blight', 'powdery_mildew', 'leaf_spot',
            'bacterial_spot', 'viral_infection', 'fungal_infection',
            'aphids', 'whiteflies', 'thrips', 'spider_mites', 'caterpillars',
            'nutrient_deficiency', 'water_stress', 'heat_stress', 'salt_stress', 'light_stress'
        ]
        
        per_label_f1 = f1_score(all_labels, binary_predictions, average=None, zero_division=0)
        for i, name in enumerate(label_names):
            if i < len(per_label_f1):
                metrics[f'f1_{name}'] = per_label_f1[i]
        
        return metrics
    
    def evaluate_per_class(self, data_loader, label_names: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Evaluate metrics per class/label
        
        Args:
            data_loader: Data loader
            label_names: List of label names
        
        Returns:
            Dictionary with per-class metrics
        """
        all_predictions = []
        all_labels = []
        
        with torch.no_grad():
            for images, labels in tqdm(data_loader, desc="Per-class evaluation"):
                images = images.to(self.device)
                outputs = self.model(images)
                
                if 'multi_label' in outputs:
                    multi_label_pred = torch.sigmoid(outputs['multi_label']).cpu().numpy()
                    multi_label_true = labels['multi_label'].numpy()
                elif 'diseases' in outputs:
                    disease_pred = torch.sigmoid(outputs['diseases']).cpu().numpy()
                    pest_pred = torch.sigmoid(outputs['pests']).cpu().numpy()
                    abiotic_pred = torch.sigmoid(outputs['abiotic']).cpu().numpy()
                    multi_label_pred = np.concatenate([disease_pred, pest_pred, abiotic_pred], axis=1)
                    multi_label_true = labels['multi_label'].numpy()
                
                all_predictions.append(multi_label_pred)
                all_labels.append(multi_label_true)
        
        all_predictions = np.vstack(all_predictions)
        all_labels = np.vstack(all_labels)
        binary_predictions = (all_predictions >= 0.5).astype(int)
        
        per_class_metrics = {}
        for i, name in enumerate(label_names):
            if i < all_labels.shape[1]:
                per_class_metrics[name] = {
                    'precision': precision_score(all_labels[:, i], binary_predictions[:, i], zero_division=0),
                    'recall': recall_score(all_labels[:, i], binary_predictions[:, i], zero_division=0),
                    'f1': f1_score(all_labels[:, i], binary_predictions[:, i], zero_division=0),
                    'support': int(all_labels[:, i].sum())
                }
        
        return per_class_metrics


class SeverityEvaluator:
    """Evaluator for severity estimation"""
    
    def __init__(self, model: nn.Module, device: str = 'cuda'):
        self.model = model.to(device)
        self.device = device
        self.model.eval()
    
    def evaluate(self, data_loader) -> Dict[str, float]:
        """Evaluate severity predictions"""
        all_predictions = []
        all_labels = []
        
        with torch.no_grad():
            for images, labels in tqdm(data_loader, desc="Severity evaluation"):
                images = images.to(self.device)
                outputs = self.model(images)
                
                severity_pred = outputs['severity'].cpu().numpy()
                severity_true = labels['severity'].numpy()
                
                all_predictions.append(severity_pred)
                all_labels.append(severity_true)
        
        all_predictions = np.concatenate(all_predictions)
        all_labels = np.concatenate(all_labels)
        
        # Regression metrics
        mae = mean_absolute_error(all_labels, all_predictions)
        rmse = np.sqrt(mean_squared_error(all_labels, all_predictions))
        
        # Classification metrics (round to nearest integer)
        pred_classes = np.round(all_predictions).clip(0, 3).astype(int)
        true_classes = all_labels.astype(int)
        
        accuracy = accuracy_score(true_classes, pred_classes)
        
        return {
            'mae': mae,
            'rmse': rmse,
            'accuracy': accuracy
        }


def print_metrics(metrics: Dict[str, float], title: str = "Evaluation Metrics"):
    """Pretty print metrics"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"{key:30s}: {value:.4f}")
        else:
            print(f"{key:30s}: {value}")


def save_metrics_to_file(metrics: Dict[str, float], filepath: str):
    """Save metrics to a text file"""
    with open(filepath, 'w') as f:
        f.write("Evaluation Metrics\n")
        f.write("="*50 + "\n")
        for key, value in metrics.items():
            if isinstance(value, float):
                f.write(f"{key:30s}: {value:.4f}\n")
            else:
                f.write(f"{key:30s}: {value}\n")


if __name__ == "__main__":
    print("Evaluation module loaded successfully")
