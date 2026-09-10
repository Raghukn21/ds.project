"""
FastAPI Application for AgriGuard AI
REST API for plant health assessment
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse, HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional
import io
import base64
import sys
import os
import numpy as np
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.dirname(__file__))

from src.inference import PlantHealthInference
from src.advisory import AdvisoryEngine
from src.plant_validator import PlantImageValidator
from src.fallback_predictor import FallbackPredictor
from src.report_generator import ReportGenerator
from schemas import (
    PredictionRequest,
    PredictionResponse,
    AdvisoryRequest,
    AdvisoryResponse
)

app = FastAPI(
    title="AgriGuard AI API",
    description="Full-Plant Health Assessment System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Serve frontend HTML
@app.get("/frontend", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend HTML"""
    with open("frontend/index.html", "r") as f:
        return f.read()

# Global variables for models
inference_engine = None
advisory_engine = None
plant_validator = None
fallback_predictor = None
report_generator = None


@app.on_event("startup")
async def startup_event():
    """Load models on startup"""
    global inference_engine, advisory_engine, plant_validator, fallback_predictor, report_generator
    
    # Initialize advisory engine (doesn't require model loading)
    advisory_engine = AdvisoryEngine()
    
    # Initialize plant validator
    plant_validator = PlantImageValidator()
    
    # Initialize fallback predictor for when no trained model is available
    fallback_predictor = FallbackPredictor()
    
    # Initialize report generator
    report_generator = ReportGenerator()
    
    # Note: Inference engine will be loaded when model checkpoint is available
    print("API server started. Advisory engine, plant validator, fallback predictor, and report generator ready.")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend HTML at root"""
    with open("frontend/index.html", "r") as f:
        return f.read()

@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "message": "AgriGuard AI API",
        "version": "1.0.0",
        "endpoints": {
            "predict": "/predict",
            "advisory": "/advisory",
            "health": "/health",
            "load-model": "/load-model"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "inference_engine_loaded": inference_engine is not None,
        "advisory_engine_loaded": advisory_engine is not None
    }


@app.post("/load-model")
async def load_model(
    model_path: str = Form(...),
    model_type: str = Form(default="multi_label"),
    backbone: str = Form(default="efficientnet_b0"),
    use_detection: bool = Form(default=False),
    detection_model_path: Optional[str] = Form(default=None)
):
    """
    Load inference model
    
    Args:
        model_path: Path to model checkpoint
        model_type: Type of model
        backbone: Backbone architecture
        use_detection: Whether to use plant detection
        detection_model_path: Path to detection model
    """
    global inference_engine
    
    try:
        inference_engine = PlantHealthInference(
            model_path=model_path,
            model_type=model_type,
            backbone=backbone,
            use_detection=use_detection,
            detection_model_path=detection_model_path
        )
        
        return {
            "status": "success",
            "message": "Model loaded successfully",
            "model_type": model_type,
            "backbone": backbone
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")


@app.post("/predict", response_model=PredictionResponse)
async def predict(
    file: UploadFile = File(...),
    threshold: float = Form(default=0.5),
    return_visualization: bool = Form(default=False)
):
    """
    Run plant health prediction on uploaded image
    
    Args:
        file: Image file
        threshold: Prediction threshold
        return_visualization: Whether to return visualization
    
    Returns:
        Prediction results
    """
    if inference_engine is None:
        raise HTTPException(
            status_code=400,
            detail="Model not loaded. Use /load-model endpoint first."
        )
    
    try:
        # Read image
        image_data = await file.read()
        image = io.BytesIO(image_data)
        
        # Run prediction
        result = inference_engine.predict(
            image=image,
            threshold=threshold,
            return_visualization=return_visualization
        )
        
        # Convert visualization to base64 if requested
        if return_visualization and 'visualization' in result:
            import cv2
            vis = result['visualization']
            _, buffer = cv2.imencode('.jpg', cv2.cvtColor(vis, cv2.COLOR_RGB2BGR))
            vis_base64 = base64.b64encode(buffer).decode('utf-8')
            result['visualization_base64'] = vis_base64
            del result['visualization']
        
        return PredictionResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/predict-base64", response_model=PredictionResponse)
async def predict_base64(request: PredictionRequest):
    """
    Run prediction on base64-encoded image
    
    Args:
        request: Prediction request with base64 image
    
    Returns:
        Prediction results
    """
    if inference_engine is None:
        raise HTTPException(
            status_code=400,
            detail="Model not loaded. Use /load-model endpoint first."
        )
    
    try:
        result = inference_engine.predict_from_base64(
            image_base64=request.image_base64,
            threshold=request.threshold
        )
        
        return PredictionResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/advisory", response_model=AdvisoryResponse)
async def get_advisory(request: AdvisoryRequest):
    """
    Get treatment recommendations based on predictions
    
    Args:
        request: Advisory request with predictions and metadata
    
    Returns:
        Advisory recommendations
    """
    if advisory_engine is None:
        raise HTTPException(
            status_code=500,
            detail="Advisory engine not initialized"
        )
    
    try:
        advice = advisory_engine.generate_advice(
            prediction=request.prediction,
            crop_type=request.crop_type,
            environment=request.environment
        )
        
        return AdvisoryResponse(**advice)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advisory generation failed: {str(e)}")


@app.post("/predict-and-advise")
async def predict_and_advise(
    file: UploadFile = File(...),
    crop_type: str = Form(default="unknown"),
    threshold: float = Form(default=0.5),
    temperature: Optional[float] = Form(default=None),
    humidity: Optional[float] = Form(default=None),
    soil_moisture: Optional[float] = Form(default=None)
):
    """
    Combined endpoint: run prediction and get advisory
    
    Args:
        file: Image file
        crop_type: Type of crop
        threshold: Prediction threshold
        temperature: Temperature in Celsius
        humidity: Humidity percentage
        soil_moisture: Soil moisture percentage
    
    Returns:
        Combined prediction and advisory
    """
    if advisory_engine is None:
        raise HTTPException(
            status_code=500,
            detail="Advisory engine not initialized"
        )
    
    try:
        # Read and validate image
        image_data = await file.read()
        print(f"Image data size: {len(image_data)} bytes")
        
        # Convert to PIL Image for validation
        from PIL import Image
        pil_image = Image.open(io.BytesIO(image_data)).convert('RGB')
        image_array = np.array(pil_image)
        print(f"Image shape: {image_array.shape}")
        
        # Validate that image contains a plant
        if plant_validator is not None:
            is_valid, reason = plant_validator.is_plant_image(image_array)
            print(f"Plant validation: valid={is_valid}, reason={reason}")
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid image: {reason}. Please upload an image of a plant or tree only (no humans, animals, or other objects)."
                )
        
        # Use fallback predictor if no trained model is loaded
        if inference_engine is None:
            print("Using fallback predictor (no trained model loaded)")
            prediction = fallback_predictor.predict(image_array)
            prediction['using_fallback'] = True
        else:
            # Use trained inference engine
            image = io.BytesIO(image_data)
            prediction = inference_engine.predict(image=image, threshold=threshold)
            prediction['using_fallback'] = False
        
        # Build environment dict
        environment = {}
        if temperature is not None:
            environment['temperature'] = temperature
        if humidity is not None:
            environment['humidity'] = humidity
        if soil_moisture is not None:
            environment['soil_moisture'] = soil_moisture
        
        # Get advisory
        advisory = advisory_engine.generate_advice(
            prediction=prediction,
            crop_type=crop_type,
            environment=environment if environment else None
        )
        
        return {
            "prediction": prediction,
            "advisory": advisory
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction and advisory failed: {str(e)}")


@app.post("/download-report")
async def download_report(
    prediction: str = Form(...),
    advisory: str = Form(...),
    crop_type: str = Form(default="unknown")
):
    """
    Generate and download PDF report
    
    Args:
        prediction: JSON string of prediction results
        advisory: JSON string of advisory results
        crop_type: Type of plant/tree
    
    Returns:
        PDF file download
    """
    if report_generator is None:
        raise HTTPException(
            status_code=500,
            detail="Report generator not initialized"
        )
    
    try:
        import json
        prediction_dict = json.loads(prediction)
        advisory_dict = json.loads(advisory)
        
        # Generate report
        report_bytes = report_generator.generate_report(
            prediction=prediction_dict,
            advisory=advisory_dict,
            crop_type=crop_type
        )
        
        # Return as downloadable file
        return Response(
            content=report_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=agriguard_report_{crop_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            }
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
