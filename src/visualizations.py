"""
Visualization Module for AgriGuard AI
Handles Grad-CAM, bounding boxes, and other visualizations
"""

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Optional, Tuple
import matplotlib.pyplot as plt
from PIL import Image


class GradCAM:
    """
    Grad-CAM for visualizing model attention
    """
    
    def __init__(self, model: nn.Module, target_layer: str):
        """
        Args:
            model: The model to visualize
            target_layer: Name of the target layer for Grad-CAM
        """
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        # Register hooks
        self._register_hooks()
    
    def _register_hooks(self):
        """Register forward and backward hooks"""
        def forward_hook(module, input, output):
            self.activations = output.detach()
        
        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()
        
        # Find target layer
        target_module = None
        for name, module in self.model.named_modules():
            if name == self.target_layer:
                target_module = module
                break
        
        if target_module is None:
            raise ValueError(f"Layer {self.target_layer} not found in model")
        
        target_module.register_forward_hook(forward_hook)
        target_module.register_backward_hook(backward_hook)
    
    def generate_cam(
        self,
        input_tensor: torch.Tensor,
        target_class: Optional[int] = None
    ) -> np.ndarray:
        """
        Generate Grad-CAM heatmap
        
        Args:
            input_tensor: Input tensor (1, C, H, W)
            target_class: Target class index (if None, uses predicted class)
        
        Returns:
            Heatmap as numpy array
        """
        self.model.eval()
        
        # Forward pass
        output = self.model(input_tensor)
        
        # Get target class
        if target_class is None:
            if isinstance(output, dict):
                # Handle multi-output models
                if 'multi_label' in output:
                    target_class = torch.argmax(output['multi_label']).item()
                elif 'diseases' in output:
                    target_class = torch.argmax(output['diseases']).item()
                else:
                    target_class = 0
            else:
                target_class = torch.argmax(output).item()
        
        # Backward pass
        self.model.zero_grad()
        
        if isinstance(output, dict):
            # Handle multi-output models
            if 'multi_label' in output:
                output['multi_label'][0, target_class].backward(retain_graph=True)
            elif 'diseases' in output:
                output['diseases'][0, target_class].backward(retain_graph=True)
        else:
            output[0, target_class].backward(retain_graph=True)
        
        # Get gradients and activations
        gradients = self.gradients[0]  # (C, H, W)
        activations = self.activations[0]  # (C, H, W)
        
        # Calculate weights
        weights = torch.mean(gradients, dim=(1, 2))  # (C,)
        
        # Calculate CAM
        cam = torch.zeros(activations.shape[1:], dtype=torch.float32)
        for i, w in enumerate(weights):
            cam += w * activations[i]
        
        # Apply ReLU
        cam = F.relu(cam)
        
        # Resize to input size
        cam = cam.unsqueeze(0).unsqueeze(0)
        cam = F.interpolate(cam, size=(input_tensor.shape[2], input_tensor.shape[3]), mode='bilinear', align_corners=False)
        cam = cam.squeeze().cpu().numpy()
        
        # Normalize
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
        
        return cam
    
    def overlay_cam(
        self,
        image: np.ndarray,
        cam: np.ndarray,
        alpha: float = 0.5,
        colormap: int = cv2.COLORMAP_JET
    ) -> np.ndarray:
        """
        Overlay CAM heatmap on original image
        
        Args:
            image: Original image (RGB)
            cam: CAM heatmap (0-1)
            alpha: Transparency of overlay
            colormap: OpenCV colormap
        
        Returns:
            Overlayed image
        """
        # Convert CAM to uint8
        cam_uint8 = np.uint8(255 * cam)
        
        # Apply colormap
        heatmap = cv2.applyColorMap(cam_uint8, colormap)
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
        
        # Resize heatmap to match image
        heatmap = cv2.resize(heatmap, (image.shape[1], image.shape[0]))
        
        # Overlay
        overlay = cv2.addWeighted(image, 1 - alpha, heatmap, alpha, 0)
        
        return overlay


class BoundingBoxVisualizer:
    """Visualizes detection bounding boxes"""
    
    @staticmethod
    def draw_boxes(
        image: np.ndarray,
        boxes: List[Tuple[int, int, int, int]],
        labels: Optional[List[str]] = None,
        scores: Optional[List[float]] = None,
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2
    ) -> np.ndarray:
        """
        Draw bounding boxes on image
        
        Args:
            image: Input image (RGB)
            boxes: List of (x1, y1, x2, y2) boxes
            labels: Optional list of labels for each box
            scores: Optional list of confidence scores
            color: Box color (B, G, R)
            thickness: Line thickness
        
        Returns:
            Image with drawn boxes
        """
        vis_image = image.copy()
        
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box
            
            # Draw box
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, thickness)
            
            # Draw label if provided
            if labels and i < len(labels):
                label = labels[i]
                if scores and i < len(scores):
                    label = f"{label}: {scores[i]:.2f}"
                
                # Get text size
                (text_width, text_height), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
                )
                
                # Draw background for text
                cv2.rectangle(
                    vis_image,
                    (x1, y1 - text_height - baseline - 5),
                    (x1 + text_width, y1),
                    color,
                    -1
                )
                
                # Draw text
                cv2.putText(
                    vis_image, label, (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
                )
        
        return vis_image


class PredictionVisualizer:
    """Visualizes model predictions"""
    
    @staticmethod
    def create_prediction_summary(
        image: np.ndarray,
        prediction: Dict,
        save_path: Optional[str] = None
    ) -> np.ndarray:
        """
        Create a comprehensive visualization of predictions
        
        Args:
            image: Original image
            prediction: Prediction dictionary from inference
            save_path: Optional path to save visualization
        
        Returns:
            Visualization image
        """
        # Create a larger canvas
        h, w = image.shape[:2]
        canvas_h = h + 200
        canvas = np.ones((canvas_h, w, 3), dtype=np.uint8) * 255
        
        # Place image at top
        canvas[:h, :w] = image
        
        # Add text information
        y_offset = h + 30
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        color = (0, 0, 0)
        thickness = 1
        
        # Health status
        health_text = f"Health Status: {prediction['health_status'].upper()}"
        cv2.putText(canvas, health_text, (20, y_offset), font, font_scale, color, thickness)
        y_offset += 30
        
        # Severity
        severity_text = f"Severity: {prediction['severity_level']} ({prediction['severity']:.1f}/3.0)"
        cv2.putText(canvas, severity_text, (20, y_offset), font, font_scale, color, thickness)
        y_offset += 30
        
        # Diseases
        if prediction['diseases']:
            disease_text = f"Diseases: {', '.join(prediction['diseases'][:3])}"
            cv2.putText(canvas, disease_text, (20, y_offset), font, font_scale, (0, 0, 255), thickness)
            y_offset += 30
        
        # Pests
        if prediction['pests']:
            pest_text = f"Pests: {', '.join(prediction['pests'][:3])}"
            cv2.putText(canvas, pest_text, (20, y_offset), font, font_scale, (0, 128, 0), thickness)
            y_offset += 30
        
        # Abiotic stresses
        if prediction['abiotic_stresses']:
            abiotic_text = f"Abiotic: {', '.join(prediction['abiotic_stresses'][:3])}"
            cv2.putText(canvas, abiotic_text, (20, y_offset), font, font_scale, (128, 0, 128), thickness)
        
        if save_path:
            cv2.imwrite(save_path, cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR))
        
        return canvas
    
    @staticmethod
    def create_comparison_grid(
        images: List[np.ndarray],
        titles: List[str],
        predictions: Optional[List[Dict]] = None,
        save_path: Optional[str] = None
    ) -> np.ndarray:
        """
        Create a grid comparison of multiple images
        
        Args:
            images: List of images
            titles: List of titles for each image
            predictions: Optional list of predictions
            save_path: Optional path to save
        
        Returns:
            Grid image
        """
        n_images = len(images)
        if n_images == 0:
            return np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Determine grid size
        n_cols = min(4, n_images)
        n_rows = (n_images + n_cols - 1) // n_cols
        
        # Get image size
        img_h, img_w = images[0].shape[:2]
        
        # Create grid
        grid = np.ones((n_rows * (img_h + 50), n_cols * (img_w + 20), 3), dtype=np.uint8) * 255
        
        for i, (img, title) in enumerate(zip(images, titles)):
            row = i // n_cols
            col = i % n_cols
            
            y_start = row * (img_h + 50) + 30
            x_start = col * (img_w + 20) + 10
            
            # Place image
            grid[y_start:y_start+img_h, x_start:x_start+img_w] = img
            
            # Add title
            if predictions and i < len(predictions):
                pred = predictions[i]
                title = f"{title}: {pred['health_status']}"
            
            cv2.putText(
                grid, title, (x_start, y_start - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1
            )
        
        if save_path:
            cv2.imwrite(save_path, cv2.cvtColor(grid, cv2.COLOR_RGB2BGR))
        
        return grid


def create_error_analysis_plot(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    label_names: List[str],
    save_path: Optional[str] = None
):
    """
    Create error analysis plot
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        label_names: List of label names
        save_path: Optional path to save plot
    """
    from sklearn.metrics import confusion_matrix
    import seaborn as sns
    
    # Calculate confusion matrix for each label
    fig, axes = plt.subplots(4, 5, figsize=(20, 16))
    axes = axes.flatten()
    
    for i, label_name in enumerate(label_names[:20]):
        if i >= len(axes):
            break
        
        cm = confusion_matrix(y_true[:, i], y_pred[:, i])
        sns.heatmap(cm, annot=True, fmt='d', ax=axes[i], cmap='Blues')
        axes[i].set_title(label_name)
        axes[i].set_xlabel('Predicted')
        axes[i].set_ylabel('True')
    
    # Hide unused subplots
    for i in range(len(label_names), len(axes)):
        axes[i].axis('off')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    plt.close()


if __name__ == "__main__":
    print("Visualization module loaded successfully")
