"""
Training Module for AgriGuard AI
Handles training of multi-label classification and severity models
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.tensorboard import SummaryWriter
from typing import Dict, Optional, Callable
import os
from tqdm import tqdm
import numpy as np

from .models import get_model
from .data_loader import get_data_loaders


class Trainer:
    """Trainer class for multi-label plant health models"""
    
    def __init__(
        self,
        model: nn.Module,
        train_loader,
        val_loader,
        device: str = 'cuda',
        learning_rate: float = 1e-4,
        weight_decay: float = 1e-5,
        log_dir: str = 'experiments/logs'
    ):
        """
        Args:
            model: Model to train
            train_loader: Training data loader
            val_loader: Validation data loader
            device: Device to train on
            learning_rate: Learning rate
            weight_decay: Weight decay for regularization
            log_dir: Directory for tensorboard logs
        """
        self.model = model.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.device = device
        self.log_dir = log_dir
        
        # Optimizer
        self.optimizer = optim.AdamW(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer, T_max=50, eta_min=1e-6
        )
        
        # Loss functions
        self.multi_label_criterion = nn.BCEWithLogitsLoss()
        self.health_criterion = nn.CrossEntropyLoss()
        self.severity_criterion = nn.MSELoss()
        
        # Tensorboard writer
        self.writer = SummaryWriter(log_dir)
        
        self.best_val_loss = float('inf')
    
    def train_epoch(self, epoch: int) -> Dict[str, float]:
        """Train for one epoch"""
        self.model.train()
        
        total_loss = 0
        multi_label_loss = 0
        health_loss = 0
        severity_loss = 0
        
        pbar = tqdm(self.train_loader, desc=f"Epoch {epoch}")
        for batch_idx, (images, labels) in enumerate(pbar):
            images = images.to(self.device)
            
            # Move labels to device
            multi_label = labels['multi_label'].to(self.device)
            health_status = labels['health_status'].to(self.device)
            severity = labels['severity'].to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(images)
            
            # Calculate losses
            if 'multi_label' in outputs:
                ml_loss = self.multi_label_criterion(outputs['multi_label'], multi_label)
            elif 'diseases' in outputs:
                # Multi-head model
                disease_loss = self.multi_label_criterion(outputs['diseases'], multi_label[:, :7])
                pest_loss = self.multi_label_criterion(outputs['pests'], multi_label[:, 7:12])
                abiotic_loss = self.multi_label_criterion(outputs['abiotic'], multi_label[:, 12:])
                ml_loss = disease_loss + pest_loss + abiotic_loss
            else:
                ml_loss = torch.tensor(0.0, device=self.device)
            
            h_loss = self.health_criterion(outputs['health_status'], health_status)
            s_loss = self.severity_criterion(outputs['severity'], severity)
            
            # Combined loss
            loss = ml_loss + 0.5 * h_loss + 0.3 * s_loss
            
            # Backward pass
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()
            
            # Track losses
            total_loss += loss.item()
            multi_label_loss += ml_loss.item()
            health_loss += h_loss.item()
            severity_loss += s_loss.item()
            
            pbar.set_postfix({
                'loss': loss.item(),
                'ml_loss': ml_loss.item(),
                'h_loss': h_loss.item(),
                's_loss': s_loss.item()
            })
        
        # Calculate averages
        num_batches = len(self.train_loader)
        return {
            'total_loss': total_loss / num_batches,
            'multi_label_loss': multi_label_loss / num_batches,
            'health_loss': health_loss / num_batches,
            'severity_loss': severity_loss / num_batches
        }
    
    def validate(self, epoch: int) -> Dict[str, float]:
        """Validate the model"""
        self.model.eval()
        
        total_loss = 0
        multi_label_loss = 0
        health_loss = 0
        severity_loss = 0
        
        with torch.no_grad():
            for images, labels in tqdm(self.val_loader, desc="Validation"):
                images = images.to(self.device)
                
                multi_label = labels['multi_label'].to(self.device)
                health_status = labels['health_status'].to(self.device)
                severity = labels['severity'].to(self.device)
                
                outputs = self.model(images)
                
                # Calculate losses
                if 'multi_label' in outputs:
                    ml_loss = self.multi_label_criterion(outputs['multi_label'], multi_label)
                elif 'diseases' in outputs:
                    disease_loss = self.multi_label_criterion(outputs['diseases'], multi_label[:, :7])
                    pest_loss = self.multi_label_criterion(outputs['pests'], multi_label[:, 7:12])
                    abiotic_loss = self.multi_label_criterion(outputs['abiotic'], multi_label[:, 12:])
                    ml_loss = disease_loss + pest_loss + abiotic_loss
                else:
                    ml_loss = torch.tensor(0.0, device=self.device)
                
                h_loss = self.health_criterion(outputs['health_status'], health_status)
                s_loss = self.severity_criterion(outputs['severity'], severity)
                
                loss = ml_loss + 0.5 * h_loss + 0.3 * s_loss
                
                total_loss += loss.item()
                multi_label_loss += ml_loss.item()
                health_loss += h_loss.item()
                severity_loss += s_loss.item()
        
        num_batches = len(self.val_loader)
        return {
            'total_loss': total_loss / num_batches,
            'multi_label_loss': multi_label_loss / num_batches,
            'health_loss': health_loss / num_batches,
            'severity_loss': severity_loss / num_batches
        }
    
    def train(self, num_epochs: int, save_dir: str = 'experiments/checkpoints'):
        """Train the model for multiple epochs"""
        os.makedirs(save_dir, exist_ok=True)
        
        for epoch in range(1, num_epochs + 1):
            # Train
            train_metrics = self.train_epoch(epoch)
            
            # Validate
            val_metrics = self.validate(epoch)
            
            # Update learning rate
            self.scheduler.step()
            
            # Log to tensorboard
            for key, value in train_metrics.items():
                self.writer.add_scalar(f'train/{key}', value, epoch)
            for key, value in val_metrics.items():
                self.writer.add_scalar(f'val/{key}', value, epoch)
            
            self.writer.add_scalar('learning_rate', self.optimizer.param_groups[0]['lr'], epoch)
            
            print(f"\nEpoch {epoch}/{num_epochs}")
            print(f"Train Loss: {train_metrics['total_loss']:.4f}")
            print(f"Val Loss: {val_metrics['total_loss']:.4f}")
            
            # Save best model
            if val_metrics['total_loss'] < self.best_val_loss:
                self.best_val_loss = val_metrics['total_loss']
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': self.model.state_dict(),
                    'optimizer_state_dict': self.optimizer.state_dict(),
                    'val_loss': val_metrics['total_loss']
                }, os.path.join(save_dir, 'best_model.pth'))
                print(f"Saved best model with val_loss: {val_metrics['total_loss']:.4f}")
            
            # Save checkpoint
            if epoch % 5 == 0:
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': self.model.state_dict(),
                    'optimizer_state_dict': self.optimizer.state_dict(),
                    'val_loss': val_metrics['total_loss']
                }, os.path.join(save_dir, f'checkpoint_epoch_{epoch}.pth'))
        
        self.writer.close()


def train_model(
    data_dir: str,
    metadata_file: str,
    model_type: str = 'multi_label',
    backbone: str = 'efficientnet_b0',
    num_epochs: int = 50,
    batch_size: int = 32,
    learning_rate: float = 1e-4,
    device: str = 'cuda',
    num_workers: int = 4
):
    """
    Main training function
    
    Args:
        data_dir: Directory containing images
        metadata_file: Path to metadata CSV
        model_type: Type of model to train
        backbone: Backbone architecture
        num_epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Learning rate
        device: Device to train on
        num_workers: Number of data loading workers
    """
    # Get data loaders
    data_loaders = get_data_loaders(
        data_dir=data_dir,
        metadata_file=metadata_file,
        batch_size=batch_size,
        num_workers=num_workers
    )
    
    # Create model kwargs based on model type
    model_kwargs = {}
    if model_type == 'multi_label':
        model_kwargs = {
            'num_diseases': 7,
            'num_pests': 5,
            'num_abiotic': 5
        }
    elif model_type == 'single_stage':
        model_kwargs = {
            'num_labels': 17
        }
    
    # Create model
    model = get_model(model_type=model_type, backbone=backbone, **model_kwargs)
    
    # Create trainer
    trainer = Trainer(
        model=model,
        train_loader=data_loaders['train'],
        val_loader=data_loaders['val'],
        device=device,
        learning_rate=learning_rate
    )
    
    # Train
    trainer.train(num_epochs=num_epochs)
    
    return model


if __name__ == "__main__":
    # Example training command
    print("Training module loaded successfully")
    # To train: python src/train.py --data_dir data/raw --metadata_file data/raw/metadata.csv
