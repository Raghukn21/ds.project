# AgriGuard AI - Full-Plant Health Assessment System

A comprehensive AI-powered system for assessing plant health using full-plant images. The system detects diseases, pests, and abiotic stresses, provides severity estimates, and generates actionable treatment recommendations.

## 🌱 Features

- **Full-Plant Analysis**: Analyzes entire plant images, not just leaf patches
- **Multi-Label Classification**: Detects multiple issues simultaneously (diseases, pests, abiotic stresses)
- **Severity Estimation**: Predicts severity levels (0-3 scale) for detected issues
- **Health Status Assessment**: Classifies plants as healthy, stressed, or diseased
- **Treatment Recommendations**: Provides chemical, biological, and cultural treatment options
- **Preventive Measures**: Suggests practices to prevent future issues
- **Expert Consultation Alerts**: Indicates when professional help is needed
- **REST API**: FastAPI-based backend for easy integration
- **Web Interface**: Modern, responsive frontend for user interaction
- **Object Detection**: Optional YOLO-based plant detection and cropping

## 🏗️ Architecture

```
User uploads full-plant image (+ optional metadata)
           ↓
[Preprocessing Module]
- Resize, normalize
- Optional: object detection to crop plant
           ↓
[Core AI Model]
- Backbone: CNN or Vision Transformer (EfficientNet, ResNet, Swin)
- Heads:
  • Health status (healthy / diseased / stressed)
  • Disease type(s) (multi-label)
  • Pest presence/type
  • Abiotic stress indicators
  • Severity score
           ↓
[Decision & Advisory Engine]
- Rule-based / simple ML
- Uses:
  • Predicted labels + severity
  • Crop type, growth stage, environment (if provided)
- Outputs:
  • Diagnosis summary
  • Treatment plan
  • Prevention tips
  • When to seek expert help
           ↓
[UI / API]
- Web/mobile interface showing:
  • Image with highlights (optional Grad-CAM / bounding boxes)
  • Diagnosis & severity
  • Step-by-step recommendations
```

## 📁 Project Structure

```
agriguard-ai/
├─ data/
│  ├─ raw/
│  │  ├─ full_plant_images/
│  │  └─ metadata.csv
│  ├─ processed/
│  └─ splits/
│
├─ notebooks/
│  ├─ 01_data_exploration_full_plant.ipynb
│  ├─ 02_object_detection_for_plant_crop.ipynb
│  ├─ 03_multi_label_classification.ipynb
│  ├─ 04_severity_modeling.ipynb
│  └─ 05_error_analysis_and_visualization.ipynb
│
├─ src/
│  ├─ __init__.py
│  ├─ data_loader.py          # Data loading and preprocessing
│  ├─ preprocessing.py        # Image preprocessing and augmentation
│  ├─ detection.py            # YOLO-based plant detection
│  ├─ models.py               # Model architectures
│  ├─ train.py                # Training logic
│  ├─ evaluate.py             # Evaluation metrics
│  ├─ inference.py            # Inference engine
│  ├─ advisory.py             # Treatment recommendations
│  └─ visualizations.py       # Grad-CAM and visualizations
│
├─ api/
│  ├─ app.py                  # FastAPI application
│  └─ schemas.py              # Pydantic schemas
│
├─ frontend/
│  ├─ index.html              # Main web interface
│  └─ static/
│     ├─ css/
│     │  └─ style.css
│     └─ js/
│        └─ app.js
│
├─ experiments/
│  ├─ configs/
│  ├─ logs/
│  └─ checkpoints/
│
├─ reports/
│  ├─ figures/
│  └─ final_report.pdf
│
├─ requirements.txt
├─ README.md
└─ .gitignore
```

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- CUDA-capable GPU (optional, for faster training)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd agriguard-ai
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## 📊 Data Preparation

### Dataset Structure

Your dataset should include:
- Full-plant images (not just cropped leaves)
- Metadata CSV with the following columns:
  - `image_id`: Unique identifier for each image
  - `image_path`: Path to the image file
  - `split`: One of 'train', 'val', or 'test'
  - `crop_type`: Type of crop (tomato, chili, cotton, etc.)
  - `growth_stage`: Growth stage (vegetative, flowering, fruiting)
  - `health_status`: One of 'healthy', 'stressed', 'diseased'
  - `severity`: Severity score (0-3)
  - Disease labels: `early_blight`, `late_blight`, `powdery_mildew`, `leaf_spot`, `bacterial_spot`, `viral_infection`, `fungal_infection`
  - Pest labels: `aphids`, `whiteflies`, `thrips`, `spider_mites`, `caterpillars`
  - Abiotic labels: `nutrient_deficiency`, `water_stress`, `heat_stress`, `salt_stress`, `light_stress`

### Sample Metadata

A sample metadata file can be generated using:
```python
from src.data_loader import create_sample_metadata
create_sample_metadata("data/raw/metadata.csv")
```

## 🎯 Training

### Train Multi-Label Classification Model

```python
from src.train import train_model

model = train_model(
    data_dir='data/raw',
    metadata_file='data/raw/metadata.csv',
    model_type='multi_label',
    backbone='efficientnet_b0',
    num_epochs=50,
    batch_size=32,
    learning_rate=1e-4,
    device='cuda'
)
```

### Train YOLO Detection Model (Optional)

```python
from src.detection import train_yolo_model

results = train_yolo_model(
    data_yaml='data/detection_data.yaml',
    epochs=100,
    batch_size=16,
    image_size=640,
    model_name='yolov8n.pt'
)
```

## 🔮 Inference

### Python API

```python
from src.inference import load_inference_engine
from src.advisory import create_advisory_engine

# Load inference engine
inference = load_inference_engine(
    model_path='experiments/checkpoints/best_model.pth',
    model_type='multi_label',
    backbone='efficientnet_b0'
)

# Load advisory engine
advisory = create_advisory_engine()

# Run prediction
prediction = inference.predict('path/to/plant/image.jpg')

# Get recommendations
advice = advisory.generate_advice(
    prediction=prediction,
    crop_type='tomato',
    environment={'temperature': 28, 'humidity': 75}
)
```

### REST API

Start the API server:
```bash
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

Load the model:
```bash
curl -X POST "http://localhost:8000/load-model" \
  -F "model_path=experiments/checkpoints/best_model.pth" \
  -F "model_type=multi_label" \
  -F "backbone=efficientnet_b0"
```

Run prediction:
```bash
curl -X POST "http://localhost:8000/predict-and-advise" \
  -F "file=@path/to/image.jpg" \
  -F "crop_type=tomato" \
  -F "threshold=0.5"
```

### Web Interface

1. Start the API server
2. Open `frontend/index.html` in a web browser
3. Upload an image and select options
4. Click "Analyze Plant Health"

## 📈 Evaluation

### Evaluate Model Performance

```python
from src.evaluate import MultiLabelEvaluator
from src.data_loader import get_data_loaders
from src.models import get_model
import torch

# Load data
data_loaders = get_data_loaders(
    data_dir='data/raw',
    metadata_file='data/raw/metadata.csv'
)

# Load model
model = get_model('multi_label', backbone='efficientnet_b0')
checkpoint = torch.load('experiments/checkpoints/best_model.pth')
model.load_state_dict(checkpoint['model_state_dict'])

# Evaluate
evaluator = MultiLabelEvaluator(model, device='cuda')
metrics = evaluator.evaluate(data_loaders['test'])

print(metrics)
```

### Metrics

- **Multi-label metrics**: Precision, Recall, F1 (macro/micro), Hamming loss
- **Detection metrics**: mAP@0.5, mAP@0.5:0.95 (if using YOLO)
- **Severity metrics**: MAE, RMSE, R² score
- **Health status**: Classification accuracy

## 🧪 Notebooks

The project includes Jupyter notebooks for data exploration and analysis:

1. **01_data_exploration_full_plant.ipynb**: Explore dataset distribution and characteristics
2. **02_object_detection_for_plant_crop.ipynb**: Plant detection and cropping experiments
3. **03_multi_label_classification.ipynb**: Train and evaluate multi-label models
4. **04_severity_modeling.ipynb**: Severity estimation experiments
5. **05_error_analysis_and_visualization.ipynb**: Comprehensive error analysis

## 🎨 Model Architectures

### Multi-Label Classifier
- **Backbone**: EfficientNet-B0/B3, ResNet50, or Vision Transformer
- **Heads**: 
  - Disease classification (7 classes)
  - Pest classification (5 classes)
  - Abiotic stress classification (5 classes)
  - Health status (3 classes)
  - Severity estimation (regression)

### Single-Stage Model
- Simplified architecture with single multi-label output layer
- Suitable for smaller datasets or faster inference

### Two-Stage Pipeline
- Stage 1: YOLO-based plant detection
- Stage 2: Multi-label classification on cropped plant region
- Reduces background noise

## 🌍 Supported Crops

- Tomato
- Chili
- Cotton
- Potato
- Rice
- Wheat
- Maize
- (Extensible to other crops)

## 🐛 Detected Issues

### Diseases
- Early blight
- Late blight
- Powdery mildew
- Leaf spot
- Bacterial spot
- Viral infection
- Fungal infection

### Pests
- Aphids
- Whiteflies
- Thrips
- Spider mites
- Caterpillars

### Abiotic Stresses
- Nutrient deficiency
- Water stress
- Heat stress
- Salt stress
- Light stress

## 📝 API Endpoints

- `GET /`: API information
- `GET /health`: Health check
- `POST /load-model`: Load inference model
- `POST /predict`: Run prediction on uploaded image
- `POST /predict-base64`: Run prediction on base64-encoded image
- `POST /advisory`: Get treatment recommendations
- `POST /predict-and-advise`: Combined prediction and advisory

## 🔧 Configuration

### Model Configuration

Model configurations can be adjusted in `experiments/configs/`:
- Backbone selection
- Number of classes
- Learning rate
- Batch size
- Image size

### Training Configuration

Training parameters can be modified in `src/train.py`:
- Number of epochs
- Loss weights
- Optimizer settings
- Learning rate schedule

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- PlantVillage dataset for inspiration
- Ultralytics for YOLO implementation
- PyTorch team for the deep learning framework

## 📞 Contact

For questions or support, please open an issue on GitHub.

## 🗺️ Roadmap

- [ ] Add more crop types
- [ ] Implement Vision Transformer backbone
- [ ] Add mobile app support
- [ ] Integrate weather data API
- [ ] Multi-language support
- [ ] User authentication and history
- [ ] Community features for sharing diagnoses

## ⚠️ Disclaimer

This system provides recommendations based on AI analysis and should not replace professional agricultural advice. Always consult with agricultural experts for critical decisions.
