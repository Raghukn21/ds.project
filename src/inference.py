"""
Inference Module for AgriGuard AI
Handles model inference on new images
"""

import torch
import torch.nn as nn
import cv2
import numpy as np
from PIL import Image
from typing import Dict, List, Optional, Union
import io
import base64

from .models import get_model
from .preprocessing import ImagePreprocessor, PlantCropper
from .detection import PlantDetector


class PlantHealthInference:
    """Inference engine for plant health assessment"""
    
    def __init__(
        self,
        model_path: str,
        model_type: str = 'multi_label',
        backbone: str = 'efficientnet_b0',
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
        use_detection: bool = False,
        detection_model_path: Optional[str] = None
    ):
        """
        Args:
            model_path: Path to trained model checkpoint
            model_type: Type of model ('multi_label', 'single_stage')
            backbone: Backbone architecture
            device: Device to run inference on
            use_detection: Whether to use plant detection before classification
            detection_model_path: Path to detection model (if use_detection=True)
        """
        self.device = device
        self.model_type = model_type
        self.use_detection = use_detection
        
        # Load classification model
        self.model = self._load_model(model_path, model_type, backbone)
        self.model.eval()
        
        # Load detection model if specified
        if use_detection and detection_model_path:
            self.detector = PlantDetector(model_path=detection_model_path, device=device)
        else:
            self.detector = None
        
        # Preprocessor
        self.preprocessor = ImagePreprocessor(image_size=224)
        
        # Label names
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
        self.health_status_labels = ['healthy', 'stressed', 'diseased']
    
    def _load_model(self, model_path: str, model_type: str, backbone: str) -> nn.Module:
        """Load model from checkpoint"""
        # Create model
        model_kwargs = {}
        if model_type == 'multi_label':
            model_kwargs = {'num_diseases': 7, 'num_pests': 5, 'num_abiotic': 5}
        elif model_type == 'single_stage':
            model_kwargs = {'num_labels': 17}
        
        model = get_model(model_type=model_type, backbone=backbone, **model_kwargs)
        
        # Load checkpoint
        checkpoint = torch.load(model_path, map_location=self.device)
        model.load_state_dict(checkpoint['model_state_dict'])
        
        return model
    
    def preprocess_image(self, image: Union[str, np.ndarray, Image.Image, io.BytesIO]) -> np.ndarray:
        """
        Preprocess image for inference
        
        Args:
            image: Image as file path, numpy array, PIL Image, or BytesIO
        
        Returns:
            Preprocessed image as numpy array
        """
        if isinstance(image, str):
            # Load from file path
            image = cv2.imread(image)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        elif isinstance(image, Image.Image):
            # Convert PIL to numpy
            image = np.array(image.convert('RGB'))
        elif isinstance(image, io.BytesIO):
            # Load from BytesIO
            image = Image.open(image)
            image = np.array(image.convert('RGB'))
        elif not isinstance(image, np.ndarray):
            # Try to convert to numpy array
            image = np.array(image)
        
        return image
    
    def predict(
        self,
        image: Union[str, np.ndarray, Image.Image],
        threshold: float = 0.5,
        return_visualization: bool = False
    ) -> Dict:
        """
        Run inference on a single image
        
        Args:
            image: Input image
            threshold: Threshold for binary predictions
            return_visualization: Whether to return visualization
        
        Returns:
            Dictionary with predictions:
            - health_status: str
            - diseases: List[str]
            - pests: List[str]
            - abiotic_stresses: List[str]
            - severity: float
            - confidence: Dict
            - visualization: Optional image
        """
        # Preprocess image
        image_array = self.preprocess_image(image)
        
        # Optional: Detect and crop plant
        if self.use_detection and self.detector:
            cropped_image, detections = self.detector.detect_and_crop(image_array)
            image_to_process = cropped_image
        else:
            image_to_process = image_array
            detections = None
        
        # Apply preprocessing transforms
        processed = self.preprocessor.preprocess_val(image_to_process)
        processed = processed.unsqueeze(0).to(self.device)
        
        # Run inference
        with torch.no_grad():
            outputs = self.model(processed)
        
        # Parse outputs
        if 'multi_label' in outputs:
            multi_label_probs = torch.sigmoid(outputs['multi_label']).cpu().numpy()[0]
        elif 'diseases' in outputs:
            disease_probs = torch.sigmoid(outputs['diseases']).cpu().numpy()[0]
            pest_probs = torch.sigmoid(outputs['pests']).cpu().numpy()[0]
            abiotic_probs = torch.sigmoid(outputs['abiotic']).cpu().numpy()[0]
            multi_label_probs = np.concatenate([disease_probs, pest_probs, abiotic_probs])
        else:
            multi_label_probs = np.zeros(len(self.all_labels))
        
        health_probs = torch.softmax(outputs['health_status'], dim=1).cpu().numpy()[0]
        severity = outputs['severity'].cpu().numpy()[0]
        
        # Get binary predictions
        binary_predictions = (multi_label_probs >= threshold).astype(int)
        
        # Extract predictions by category
        diseases = [self.all_labels[i] for i in range(len(self.disease_labels)) if binary_predictions[i]]
        pests = [self.all_labels[i] for i in range(len(self.disease_labels), len(self.disease_labels) + len(self.pest_labels)) if binary_predictions[i]]
        abiotic = [self.all_labels[i] for i in range(len(self.disease_labels) + len(self.pest_labels), len(self.all_labels)) if binary_predictions[i]]
        
        # Health status
        health_status_idx = np.argmax(health_probs)
        health_status = self.health_status_labels[health_status_idx]
        
        # Build result
        result = {
            'health_status': health_status,
            'diseases': diseases,
            'pests': pests,
            'abiotic_stresses': abiotic,
            'severity': float(severity),
            'severity_level': self._get_severity_level(severity),
            'confidence': {
                'health_status': float(health_probs[health_status_idx]),
                'diseases': {label: float(multi_label_probs[i]) for i, label in enumerate(self.disease_labels)},
                'pests': {label: float(multi_label_probs[i]) for i, label in enumerate(self.pest_labels, start=len(self.disease_labels))},
                'abiotic': {label: float(multi_label_probs[i]) for i, label in enumerate(self.abiotic_labels, start=len(self.disease_labels) + len(self.pest_labels))}
            }
        }
        
        # Add visualization if requested
        if return_visualization:
            result['visualization'] = self._create_visualization(
                image_array, detections, result
            )
        
        return result
    
    def _get_severity_level(self, severity: float) -> str:
        """Convert severity score to level"""
        if severity < 1.0:
            return 'low'
        elif severity < 2.0:
            return 'medium'
        else:
            return 'high'
    
    def _create_visualization(
        self,
        image: np.ndarray,
        detections: Optional[List],
        predictions: Dict
    ) -> np.ndarray:
        """Create visualization with predictions overlay"""
        vis_image = image.copy()
        
        # Draw detection boxes if available
        if detections:
            for det in detections:
                x1, y1, x2, y2 = det['bbox']
                cv2.rectangle(vis_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Add text overlay
        y_offset = 30
        cv2.putText(vis_image, f"Health: {predictions['health_status']}", 
                   (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        y_offset += 30
        cv2.putText(vis_image, f"Severity: {predictions['severity_level']} ({predictions['severity']:.1f})", 
                   (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        if predictions['diseases']:
            y_offset += 30
            cv2.putText(vis_image, f"Diseases: {', '.join(predictions['diseases'][:2])}", 
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        return vis_image
    
    def predict_batch(
        self,
        images: List[Union[str, np.ndarray, Image.Image]],
        threshold: float = 0.5
    ) -> List[Dict]:
        """
        Run inference on a batch of images
        
        Args:
            images: List of images
            threshold: Threshold for binary predictions
        
        Returns:
            List of prediction dictionaries
        """
        results = []
        for image in images:
            result = self.predict(image, threshold=threshold)
            results.append(result)
        
        return results
    
    def predict_from_base64(self, image_base64: str, threshold: float = 0.5) -> Dict:
        """
        Run inference on base64-encoded image
        
        Args:
            image_base64: Base64-encoded image string
            threshold: Threshold for binary predictions
        
        Returns:
            Prediction dictionary
        """
        # Decode base64
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data))
        
        return self.predict(image, threshold=threshold)


def load_inference_engine(
    model_path: str,
    model_type: str = 'multi_label',
    backbone: str = 'efficientnet_b0',
    device: str = 'cuda'
) -> PlantHealthInference:
    """
    Factory function to create inference engine
    
    Args:
        model_path: Path to model checkpoint
        model_type: Type of model
        backbone: Backbone architecture
        device: Device to run on
    
    Returns:
        PlantHealthInference instance
    """
    return PlantHealthInference(
        model_path=model_path,
        model_type=model_type,
        backbone=backbone,
        device=device
    )


if __name__ == "__main__":
    print("Inference module loaded successfully")
