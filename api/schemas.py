"""
Pydantic Schemas for AgriGuard AI API
Request and response models for validation
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class PredictionRequest(BaseModel):
    """Request model for prediction with base64 image"""
    image_base64: str = Field(..., description="Base64-encoded image string")
    threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Prediction threshold")
    
    class Config:
        schema_extra = {
            "example": {
                "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "threshold": 0.5
            }
        }


class ConfidenceScores(BaseModel):
    """Confidence scores for different categories"""
    health_status: float
    diseases: Dict[str, float]
    pests: Dict[str, float]
    abiotic: Dict[str, float]


class PredictionResponse(BaseModel):
    """Response model for plant health prediction"""
    health_status: str = Field(..., description="Overall health status")
    diseases: List[str] = Field(default_factory=list, description="Detected diseases")
    pests: List[str] = Field(default_factory=list, description="Detected pests")
    abiotic_stresses: List[str] = Field(default_factory=list, description="Detected abiotic stresses")
    severity: float = Field(..., description="Severity score (0-3)")
    severity_level: str = Field(..., description="Severity level (low/medium/high)")
    confidence: ConfidenceScores = Field(..., description="Confidence scores")
    visualization_base64: Optional[str] = Field(None, description="Base64-encoded visualization")
    
    class Config:
        schema_extra = {
            "example": {
                "health_status": "diseased",
                "diseases": ["early_blight"],
                "pests": [],
                "abiotic_stresses": ["nutrient_deficiency"],
                "severity": 2.1,
                "severity_level": "medium",
                "confidence": {
                    "health_status": 0.85,
                    "diseases": {"early_blight": 0.78, "late_blight": 0.12},
                    "pests": {"aphids": 0.05, "whiteflies": 0.02},
                    "abiotic": {"nutrient_deficiency": 0.65, "water_stress": 0.15}
                }
            }
        }


class AdvisoryRequest(BaseModel):
    """Request model for advisory generation"""
    prediction: Dict = Field(..., description="Prediction dictionary from inference")
    crop_type: str = Field(default="unknown", description="Type of crop")
    environment: Optional[Dict] = Field(None, description="Environment data (temp, humidity, soil_moisture)")
    
    class Config:
        schema_extra = {
            "example": {
                "prediction": {
                    "health_status": "diseased",
                    "diseases": ["early_blight"],
                    "pests": [],
                    "abiotic_stresses": [],
                    "severity": 2.1,
                    "severity_level": "medium"
                },
                "crop_type": "tomato",
                "environment": {
                    "temperature": 28.0,
                    "humidity": 75.0,
                    "soil_moisture": 60.0
                }
            }
        }


class TreatmentRecommendations(BaseModel):
    """Treatment recommendations by type"""
    chemical: List[str] = Field(default_factory=list)
    biological: List[str] = Field(default_factory=list)
    cultural: List[str] = Field(default_factory=list)


class AdvisoryResponse(BaseModel):
    """Response model for advisory recommendations"""
    summary: str = Field(..., description="Summary of diagnosis")
    priority: str = Field(..., description="Priority level (low/moderate/high/urgent)")
    treatments: TreatmentRecommendations = Field(..., description="Treatment recommendations")
    prevention: List[str] = Field(..., description="Preventive measures")
    expert_needed: bool = Field(..., description="Whether expert consultation is needed")
    environment_considerations: List[str] = Field(default_factory=list, description="Environment-based considerations")
    
    class Config:
        schema_extra = {
            "example": {
                "summary": "The tomato plant shows signs of early_blight with severity level medium (2.1/3.0). Follow the recommended treatments and preventive measures.",
                "priority": "moderate",
                "treatments": {
                    "chemical": ["Apply chlorothalonil or copper-based fungicide as per label instructions."],
                    "biological": ["Apply Bacillus subtilis or Trichoderma-based biofungicides."],
                    "cultural": ["Remove and destroy infected leaves immediately.", "Improve air circulation by proper plant spacing."]
                },
                "prevention": [
                    "Practice crop rotation with non-host crops annually.",
                    "Use disease-resistant varieties when available.",
                    "Maintain proper plant spacing for good air circulation."
                ],
                "expert_needed": False,
                "environment_considerations": [
                    "High humidity detected - be extra vigilant about fungal diseases."
                ]
            }
        }


class ModelLoadRequest(BaseModel):
    """Request model for loading a model"""
    model_path: str = Field(..., description="Path to model checkpoint")
    model_type: str = Field(default="multi_label", description="Type of model")
    backbone: str = Field(default="efficientnet_b0", description="Backbone architecture")
    use_detection: bool = Field(default=False, description="Whether to use plant detection")
    detection_model_path: Optional[str] = Field(None, description="Path to detection model")
    
    class Config:
        schema_extra = {
            "example": {
                "model_path": "experiments/checkpoints/best_model.pth",
                "model_type": "multi_label",
                "backbone": "efficientnet_b0",
                "use_detection": False
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    inference_engine_loaded: bool
    advisory_engine_loaded: bool


class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(..., description="Error message")
