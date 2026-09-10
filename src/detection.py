"""
Plant Detection Module for AgriGuard AI
Uses YOLO-based object detection to locate and crop plants in images
"""

import cv2
import numpy as np
import torch
from typing import List, Tuple, Optional, Dict
from PIL import Image


class PlantDetector:
    """
    Plant detector using YOLO architecture
    Detects plants in images and returns bounding boxes
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        """
        Args:
            model_path: Path to trained YOLO model weights
            confidence_threshold: Minimum confidence for detections
            iou_threshold: IoU threshold for NMS
            device: Device to run inference on
        """
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        self.model = None
        
        if model_path:
            self.load_model(model_path)
    
    def load_model(self, model_path: str):
        """Load YOLO model from checkpoint"""
        try:
            from ultralytics import YOLO
            self.model = YOLO(model_path)
            self.model.to(self.device)
            print(f"Model loaded from {model_path}")
        except ImportError:
            print("ultralytics package not found. Install with: pip install ultralytics")
            raise
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
    
    def detect(
        self,
        image: np.ndarray,
        return_crops: bool = False
    ) -> List[Dict]:
        """
        Detect plants in image
        
        Args:
            image: Input image as numpy array (RGB)
            return_crops: Whether to return cropped plant images
        
        Returns:
            List of detection dictionaries with keys:
                - bbox: [x1, y1, x2, y2]
                - confidence: float
                - class_id: int
                - crop: cropped image (if return_crops=True)
        """
        if self.model is None:
            # Fallback: return full image as single detection
            h, w = image.shape[:2]
            return [{
                'bbox': [0, 0, w, h],
                'confidence': 1.0,
                'class_id': 0,
                'crop': image if return_crops else None
            }]
        
        # Run inference
        results = self.model(image, conf=self.confidence_threshold, iou=self.iou_threshold)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = box.conf[0].cpu().numpy()
                class_id = int(box.cls[0].cpu().numpy())
                
                detection = {
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'confidence': float(confidence),
                    'class_id': class_id
                }
                
                if return_crops:
                    crop = image[int(y1):int(y2), int(x1):int(x2)]
                    detection['crop'] = crop
                
                detections.append(detection)
        
        return detections
    
    def detect_and_crop(
        self,
        image: np.ndarray,
        max_detections: int = 1
    ) -> Tuple[np.ndarray, List[Dict]]:
        """
        Detect plants and return cropped image(s)
        
        Args:
            image: Input image
            max_detections: Maximum number of plants to crop
        
        Returns:
            primary_crop: Main plant crop (or original if no detection)
            all_detections: List of all detections
        """
        detections = self.detect(image, return_crops=True)
        
        if not detections:
            return image, []
        
        # Sort by confidence
        detections.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Get primary crop (highest confidence)
        primary_crop = detections[0]['crop'] if detections[0]['crop'] is not None else image
        
        # Limit detections
        detections = detections[:max_detections]
        
        return primary_crop, detections
    
    def visualize_detections(
        self,
        image: np.ndarray,
        detections: List[Dict],
        save_path: Optional[str] = None
    ) -> np.ndarray:
        """
        Draw bounding boxes on image
        
        Args:
            image: Input image
            detections: List of detection dictionaries
            save_path: Optional path to save visualization
        
        Returns:
            Image with drawn bounding boxes
        """
        vis_image = image.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            conf = det['confidence']
            
            # Draw box
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label
            label = f"Plant: {conf:.2f}"
            cv2.putText(
                vis_image, label, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2
            )
        
        if save_path:
            cv2.imwrite(save_path, cv2.cvtColor(vis_image, cv2.COLOR_RGB2BGR))
        
        return vis_image


class SimplePlantDetector:
    """
    Simple plant detector using color-based segmentation
    Fallback when YOLO model is not available
    """
    
    def __init__(self, method: str = 'green_threshold'):
        """
        Args:
            method: Detection method ('green_threshold' or 'contour')
        """
        self.method = method
    
    def detect(self, image: np.ndarray) -> np.ndarray:
        """
        Detect plant region using color segmentation
        
        Returns:
            Binary mask of plant region
        """
        if self.method == 'green_threshold':
            return self._green_threshold_detection(image)
        else:
            return self._contour_detection(image)
    
    def _green_threshold_detection(self, image: np.ndarray) -> np.ndarray:
        """Detect plant using green color thresholding in HSV space"""
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        # Green range for plants
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        
        mask = cv2.inRange(hsv, lower_green, upper_green)
        
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        return mask
    
    def _contour_detection(self, image: np.ndarray) -> np.ndarray:
        """Detect plant using contour detection"""
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create mask from largest contour
        mask = np.zeros_like(gray)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            cv2.drawContours(mask, [largest_contour], -1, 255, -1)
        
        return mask
    
    def get_bounding_box(self, mask: np.ndarray) -> Tuple[int, int, int, int]:
        """Get bounding box from binary mask"""
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            return x, y, x + w, y + h
        
        h, w = mask.shape
        return 0, 0, w, h


def train_yolo_model(
    data_yaml: str,
    epochs: int = 100,
    batch_size: int = 16,
    image_size: int = 640,
    model_name: str = 'yolov8n.pt'
):
    """
    Train YOLO model for plant detection
    
    Args:
        data_yaml: Path to data.yaml configuration file
        epochs: Number of training epochs
        batch_size: Batch size
        image_size: Image size for training
        model_name: Pre-trained model to start from
    """
    try:
        from ultralytics import YOLO
        
        # Load model
        model = YOLO(model_name)
        
        # Train
        results = model.train(
            data=data_yaml,
            epochs=epochs,
            batch=batch_size,
            imgsz=image_size,
            project='experiments',
            name='plant_detection'
        )
        
        return results
    except ImportError:
        print("ultralytics package not found. Install with: pip install ultralytics")
        return None


if __name__ == "__main__":
    print("Detection module loaded successfully")
