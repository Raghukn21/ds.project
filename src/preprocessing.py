"""
Preprocessing Module for AgriGuard AI
Handles image preprocessing, augmentation, and plant detection/cropping
"""

import cv2
import numpy as np
from PIL import Image
import torch
from typing import Tuple, Optional, List
import albumentations as A
from albumentations.pytorch import ToTensorV2


class ImagePreprocessor:
    """Handles image preprocessing and augmentation"""
    
    def __init__(self, image_size: int = 224):
        self.image_size = image_size
        
        # Training augmentation pipeline
        self.train_transform = A.Compose([
            A.Resize(image_size, image_size),
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.2),
            A.RandomRotate90(p=0.5),
            A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.1, rotate_limit=15, p=0.5),
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
            A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=20, val_shift_limit=10, p=0.5),
            A.GaussNoise(var_limit=(10.0, 50.0), p=0.3),
            A.GaussianBlur(blur_limit=(3, 7), p=0.2),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ToTensorV2()
        ])
        
        # Validation/test pipeline
        self.val_transform = A.Compose([
            A.Resize(image_size, image_size),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ToTensorV2()
        ])
    
    def preprocess_train(self, image: np.ndarray) -> torch.Tensor:
        """Apply training augmentation pipeline"""
        if not isinstance(image, np.ndarray):
            image = np.array(image)
        return self.train_transform(image=image)['image']
    
    def preprocess_val(self, image: np.ndarray) -> torch.Tensor:
        """Apply validation preprocessing pipeline"""
        if not isinstance(image, np.ndarray):
            image = np.array(image)
        return self.val_transform(image=image)['image']
    
    @staticmethod
    def resize_with_aspect_ratio(
        image: np.ndarray, 
        target_size: int = 224
    ) -> np.ndarray:
        """
        Resize image while maintaining aspect ratio, padding if necessary
        """
        h, w = image.shape[:2]
        
        # Calculate scaling factor
        scale = target_size / max(h, w)
        new_h, new_w = int(h * scale), int(w * scale)
        
        # Resize
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # Create padded image
        padded = np.zeros((target_size, target_size, 3), dtype=np.uint8)
        pad_h = (target_size - new_h) // 2
        pad_w = (target_size - new_w) // 2
        padded[pad_h:pad_h+new_h, pad_w:pad_w+new_w] = resized
        
        return padded
    
    @staticmethod
    def enhance_contrast(image: np.ndarray) -> np.ndarray:
        """Enhance image contrast using CLAHE"""
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
    
    @staticmethod
    def remove_background_simple(image: np.ndarray) -> np.ndarray:
        """
        Simple background removal using color thresholding
        Works well for plants against uniform backgrounds
        """
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        # Define green range for plants
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        
        # Create mask
        mask = cv2.inRange(hsv, lower_green, upper_green)
        
        # Apply morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Apply mask
        result = cv2.bitwise_and(image, image, mask=mask)
        
        return result, mask


class PlantCropper:
    """
    Crops plant region from image using various methods
    Can be used as preprocessing step before classification
    """
    
    def __init__(self, method: str = 'color_threshold'):
        """
        Args:
            method: One of 'color_threshold', 'contour', 'mask_rcnn'
        """
        self.method = method
    
    def crop_plant(self, image: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """
        Crop plant region from image
        
        Returns:
            cropped_image: Cropped plant image
            bbox: Bounding box (x1, y1, x2, y2)
        """
        if self.method == 'color_threshold':
            return self._crop_by_color_threshold(image)
        elif self.method == 'contour':
            return self._crop_by_contour(image)
        else:
            # Return original image if method not implemented
            h, w = image.shape[:2]
            return image, (0, 0, w, h)
    
    def _crop_by_color_threshold(self, image: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """Crop using green color thresholding"""
        preprocessor = ImagePreprocessor()
        _, mask = preprocessor.remove_background_simple(image)
        
        # Find bounding box of plant region
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Get largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            # Add padding
            pad = 20
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(image.shape[1], x + w + pad)
            y2 = min(image.shape[0], y + h + pad)
            
            cropped = image[y1:y2, x1:x2]
            return cropped, (x1, y1, x2, y2)
        
        return image, (0, 0, image.shape[1], image.shape[0])
    
    def _crop_by_contour(self, image: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """Crop using contour detection with adaptive thresholding"""
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Filter by area
            min_area = image.shape[0] * image.shape[1] * 0.01
            valid_contours = [c for c in contours if cv2.contourArea(c) > min_area]
            
            if valid_contours:
                largest_contour = max(valid_contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                # Add padding
                pad = 20
                x1 = max(0, x - pad)
                y1 = max(0, y - pad)
                x2 = min(image.shape[1], x + w + pad)
                y2 = min(image.shape[0], y + h + pad)
                
                cropped = image[y1:y2, x1:x2]
                return cropped, (x1, y1, x2, y2)
        
        return image, (0, 0, image.shape[1], image.shape[0])


def batch_preprocess_images(
    images: List[np.ndarray],
    preprocessor: ImagePreprocessor,
    mode: str = 'train'
) -> torch.Tensor:
    """
    Preprocess a batch of images
    
    Args:
        images: List of images as numpy arrays
        preprocessor: ImagePreprocessor instance
        mode: 'train' or 'val'
    
    Returns:
        Batched tensor of shape (B, C, H, W)
    """
    processed = []
    for img in images:
        if mode == 'train':
            processed.append(preprocessor.preprocess_train(img))
        else:
            processed.append(preprocessor.preprocess_val(img))
    
    return torch.stack(processed)


if __name__ == "__main__":
    # Test preprocessing
    print("Preprocessing module loaded successfully")
