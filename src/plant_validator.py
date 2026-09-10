"""
Plant Image Validation Module
Validates that uploaded images contain plants/trees and filters out humans, animals, etc.
"""

import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional


class PlantImageValidator:
    """Validates that images contain plants and filters out non-plant content"""
    
    def __init__(self, green_threshold: float = 0.10, min_plant_ratio: float = 0.05):
        """
        Args:
            green_threshold: Minimum ratio of green pixels to consider as plant
            min_plant_ratio: Minimum ratio of image that should be plant-like
        """
        self.green_threshold = green_threshold
        self.min_plant_ratio = min_plant_ratio
    
    def is_plant_image(self, image: np.ndarray) -> Tuple[bool, str]:
        """
        Check if image contains a plant/tree
        
        Args:
            image: Input image as numpy array (RGB)
        
        Returns:
            (is_valid, reason) tuple
        """
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        # Define green range for plants (wider range to include various plant colors)
        lower_green = np.array([30, 30, 30])
        upper_green = np.array([100, 255, 255])
        
        # Create mask for green pixels
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        
        # Calculate green pixel ratio
        total_pixels = image.shape[0] * image.shape[1]
        green_pixels = np.sum(green_mask > 0)
        green_ratio = green_pixels / total_pixels
        
        # Check if enough green content
        if green_ratio < self.green_threshold:
            return False, f"Image does not contain enough plant content (green ratio: {green_ratio:.2f})"
        
        # Additional check: detect skin tones (to filter humans)
        if self._detect_skin_tone(hsv, green_ratio):
            return False, "Image appears to contain human skin tones"
        
        # Additional check: detect fur/animal-like colors
        if self._detect_animal_colors(hsv):
            return False, "Image appears to contain animals"
        
        # Check for typical plant patterns
        if not self._has_plant_patterns(image):
            return False, "Image does not exhibit typical plant patterns."
        
        return True, "Valid plant image"
    
    def _detect_skin_tone(self, hsv: np.ndarray, green_ratio: float) -> bool:
        """Detect if image contains skin tones (human detection)"""
        # Skin tone ranges in HSV (also catches wood, soil, terracotta)
        lower_skin = np.array([0, 20, 50])
        upper_skin = np.array([20, 255, 255])
        
        skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
        skin_ratio = np.sum(skin_mask > 0) / (hsv.shape[0] * hsv.shape[1])
        
        # If there's plenty of green (a clear plant), be extremely forgiving of "skin" colors 
        # (which might just be wood, pots, or soil). 
        if green_ratio > 0.1:
            return skin_ratio > 0.70  # Only reject if 70% of image is skin/brown
            
        # Even if not very green (e.g., brown leaves, red flowers, stems), 
        # only reject if a massive portion is skin-colored.
        return skin_ratio > 0.55
    
    def _detect_animal_colors(self, hsv: np.ndarray) -> bool:
        """Detect if image has animal-like color patterns"""
        # Brown/tan ranges (common for animals)
        lower_brown = np.array([10, 50, 50])
        upper_brown = np.array([25, 255, 255])
        
        brown_mask = cv2.inRange(hsv, lower_brown, upper_brown)
        brown_ratio = np.sum(brown_mask > 0) / (hsv.shape[0] * hsv.shape[1])
        
        # If significant brown content without green, might be animal
        green_mask = cv2.inRange(hsv, np.array([30, 30, 30]), np.array([100, 255, 255]))
        green_ratio = np.sum(green_mask > 0) / (hsv.shape[0] * hsv.shape[1])
        
        return brown_ratio > 0.5 and green_ratio < 0.05
    
    def _has_plant_patterns(self, image: np.ndarray) -> bool:
        """Check for typical plant patterns (texture, edges)"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Detect edges
        edges = cv2.Canny(gray, 50, 150)
        edge_ratio = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
        
        # Plants typically have moderate edge density
        return 0.02 < edge_ratio < 0.3
    
    def get_plant_region(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract the plant region from image
        
        Args:
            image: Input image
        
        Returns:
            Cropped plant region or None if no plant detected
        """
        is_valid, _ = self.is_plant_image(image)
        
        if not is_valid:
            return None
        
        # Use green thresholding to find plant region
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        lower_green = np.array([30, 30, 30])
        upper_green = np.array([100, 255, 255])
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        
        # Find contours
        contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
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
            
            return image[y1:y2, x1:x2]
        
        return image


def validate_plant_image(image: np.ndarray) -> Tuple[bool, str]:
    """
    Convenience function to validate plant image
    
    Args:
        image: Input image
    
    Returns:
        (is_valid, reason) tuple
    """
    validator = PlantImageValidator()
    return validator.is_plant_image(image)


if __name__ == "__main__":
    print("Plant validator module loaded")
