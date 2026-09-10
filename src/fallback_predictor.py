"""
Fallback Prediction Module
Provides rule-based predictions when trained model is not available
"""

import cv2
import numpy as np
from typing import Dict, List
import random


class FallbackPredictor:
    """Rule-based predictor for when trained model is not available"""
    
    def __init__(self):
        """Initialize fallback predictor"""
        self.disease_symptoms = {
            'early_blight': {
                'color_ranges': [(0, 50, 50), (30, 255, 255)],  # Brown/dark spots
                'patterns': ['circular_spots', 'concentric_rings']
            },
            'late_blight': {
                'color_ranges': [(0, 50, 50), (20, 255, 255)],  # Dark brown/black
                'patterns': ['water_soaked', 'white_mold']
            },
            'powdery_mildew': {
                'color_ranges': [(0, 0, 200), (30, 50, 255)],  # White/gray
                'patterns': ['powdery_coating', 'leaf_surface']
            },
            'leaf_spot': {
                'color_ranges': [(0, 100, 100), (20, 255, 255)],  # Brown spots
                'patterns': ['circular_spots', 'yellow_halo']
            }
        }
        
        self.pest_indicators = {
            'aphids': {'color': (0, 150, 150), 'size': 'small', 'pattern': 'clusters'},
            'whiteflies': {'color': (0, 0, 200), 'size': 'tiny', 'pattern': 'flying'},
            'spider_mites': {'color': (0, 100, 100), 'size': 'tiny', 'pattern': 'webbing'}
        }
    
    def predict(self, image: np.ndarray) -> Dict:
        """
        Generate rule-based prediction for plant image
        
        Args:
            image: Input image as numpy array (RGB)
        
        Returns:
            Prediction dictionary
        """
        # Analyze image characteristics
        analysis = self._analyze_image(image)
        
        # Generate predictions based on analysis
        diseases = self._predict_diseases(analysis)
        pests = self._predict_pests(analysis)
        abiotic = self._predict_abiotic(analysis)
        
        # Determine health status
        health_status = self._determine_health_status(diseases, pests, abiotic, analysis)
        
        # Estimate severity
        severity = self._estimate_severity(diseases, pests, abiotic, analysis)
        
        # Build confidence scores
        confidence = self._generate_confidence(diseases, pests, abiotic, health_status)
        
        return {
            'health_status': health_status,
            'diseases': diseases,
            'pests': pests,
            'abiotic_stresses': abiotic,
            'severity': severity,
            'severity_level': self._get_severity_level(severity),
            'confidence': confidence
        }
    
    def _analyze_image(self, image: np.ndarray) -> Dict:
        """Analyze image characteristics"""
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Color analysis
        green_ratio = self._calculate_color_ratio(hsv, [30, 30, 30], [100, 255, 255])
        yellow_ratio = self._calculate_color_ratio(hsv, [20, 50, 50], [40, 255, 255])
        brown_ratio = self._calculate_color_ratio(hsv, [0, 50, 50], [30, 255, 255])
        white_ratio = self._calculate_color_ratio(hsv, [0, 0, 200], [180, 50, 255])
        
        # Texture analysis
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
        
        # Spot detection
        spots = self._detect_spots(gray)
        
        # Overall health indicators
        brightness = np.mean(gray)
        contrast = np.std(gray)
        
        return {
            'green_ratio': green_ratio,
            'yellow_ratio': yellow_ratio,
            'brown_ratio': brown_ratio,
            'white_ratio': white_ratio,
            'edge_density': edge_density,
            'num_spots': spots,
            'brightness': brightness,
            'contrast': contrast
        }
    
    def _calculate_color_ratio(self, hsv: np.ndarray, lower: List, upper: List) -> float:
        """Calculate ratio of pixels in color range"""
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        return np.sum(mask > 0) / (hsv.shape[0] * hsv.shape[1])
    
    def _detect_spots(self, gray: np.ndarray) -> int:
        """Detect number of spots in image"""
        # Use blob detection
        detector = cv2.SimpleBlobDetector_create()
        keypoints = detector.detect(gray)
        return len(keypoints)
    
    def _predict_diseases(self, analysis: Dict) -> List[str]:
        """Predict diseases based on image analysis"""
        diseases = []
        
        # Early blight: brown spots on green background
        if analysis['brown_ratio'] > 0.05 and analysis['green_ratio'] > 0.3:
            if analysis['num_spots'] > 5:
                diseases.append('early_blight')
        
        # Late blight: dark spots, water-soaked appearance
        if analysis['brown_ratio'] > 0.1 and analysis['brightness'] < 100:
            diseases.append('late_blight')
        
        # Powdery mildew: white/gray coating
        if analysis['white_ratio'] > 0.1:
            diseases.append('powdery_mildew')
        
        # Leaf spot: circular spots with yellow halos
        if analysis['yellow_ratio'] > 0.1 and analysis['brown_ratio'] > 0.03:
            diseases.append('leaf_spot')
        
        return diseases
    
    def _predict_pests(self, analysis: Dict) -> List[str]:
        """Predict pests based on image analysis"""
        pests = []
        
        # Aphids: small clusters, yellowing
        if analysis['yellow_ratio'] > 0.15 and analysis['edge_density'] > 0.1:
            pests.append('aphids')
        
        # Whiteflies: white spots
        if analysis['white_ratio'] > 0.05 and analysis['edge_density'] > 0.15:
            pests.append('whiteflies')
        
        # Spider mites: webbing patterns (high edge density)
        if analysis['edge_density'] > 0.2:
            pests.append('spider_mites')
        
        return pests
    
    def _predict_abiotic(self, analysis: Dict) -> List[str]:
        """Predict abiotic stresses based on image analysis"""
        abiotic = []
        
        # Nutrient deficiency: yellowing leaves
        if analysis['yellow_ratio'] > 0.2 and analysis['green_ratio'] < 0.4:
            abiotic.append('nutrient_deficiency')
        
        # Water stress: wilting (low contrast, dull appearance)
        if analysis['contrast'] < 40 and analysis['brightness'] < 80:
            abiotic.append('water_stress')
        
        # Heat stress: bleaching, high brightness
        if analysis['brightness'] > 180:
            abiotic.append('heat_stress')
        
        return abiotic
    
    def _determine_health_status(self, diseases: List, pests: List, 
                                 abiotic: List, analysis: Dict) -> str:
        """Determine overall health status"""
        total_issues = len(diseases) + len(pests) + len(abiotic)
        
        if total_issues == 0:
            return 'healthy'
        elif total_issues <= 2 and analysis['green_ratio'] > 0.4:
            return 'stressed'
        else:
            return 'diseased'
    
    def _estimate_severity(self, diseases: List, pests: List, 
                          abiotic: List, analysis: Dict) -> float:
        """Estimate severity score (0-3)"""
        base_severity = 0.0
        
        # Add severity for each issue
        base_severity += len(diseases) * 0.5
        base_severity += len(pests) * 0.3
        base_severity += len(abiotic) * 0.4
        
        # Adjust based on visual indicators
        if analysis['brown_ratio'] > 0.15:
            base_severity += 0.5
        if analysis['yellow_ratio'] > 0.25:
            base_severity += 0.3
        if analysis['green_ratio'] < 0.2:
            base_severity += 0.4
        
        # Cap at 3.0
        return min(base_severity, 3.0)
    
    def _get_severity_level(self, severity: float) -> str:
        """Convert severity score to level"""
        if severity < 1.0:
            return 'low'
        elif severity < 2.0:
            return 'medium'
        else:
            return 'high'
    
    def _generate_confidence(self, diseases: List, pests: List, 
                            abiotic: List, health_status: str) -> Dict:
        """Generate confidence scores"""
        # Base confidence on number of detected issues
        total_issues = len(diseases) + len(pests) + len(abiotic)
        
        health_conf = 0.7 if total_issues == 0 else 0.6
        
        disease_conf = {d: 0.5 + random.random() * 0.3 for d in diseases}
        pest_conf = {p: 0.5 + random.random() * 0.3 for p in pests}
        abiotic_conf = {a: 0.5 + random.random() * 0.3 for a in abiotic}
        
        return {
            'health_status': health_conf,
            'diseases': disease_conf,
            'pests': pest_conf,
            'abiotic': abiotic_conf
        }


def create_fallback_predictor() -> FallbackPredictor:
    """Factory function to create fallback predictor"""
    return FallbackPredictor()


if __name__ == "__main__":
    print("Fallback predictor module loaded")
