// AgriGuard AI - Frontend JavaScript

class AgriGuardApp {
    constructor() {
        this.selectedFile = null;
        // Use origin if served by backend, otherwise default to local backend port
        const origin = window.location.origin;
        this.apiBaseUrl = (origin === 'file://' || origin === 'null' || !origin.includes(':8000')) 
            ? 'http://localhost:8000' 
            : origin;
        this.initializeElements();
        this.attachEventListeners();
    }

    initializeElements() {
        // Upload elements
        this.uploadArea = document.getElementById('uploadArea');
        this.fileInput = document.getElementById('fileInput');
        this.selectFileBtn = document.getElementById('selectFileBtn');
        this.previewContainer = document.getElementById('previewContainer');
        this.previewImage = document.getElementById('previewImage');
        this.removeImageBtn = document.getElementById('removeImageBtn');

        // Form elements
        this.cropType = document.getElementById('cropType');
        this.threshold = document.getElementById('threshold');
        this.thresholdValue = document.getElementById('thresholdValue');

        // Buttons
        this.analyzeBtn = document.getElementById('analyzeBtn');
        this.newAnalysisBtn = document.getElementById('newAnalysisBtn');
        this.downloadReportBtn = document.getElementById('downloadReportBtn');

        // Results elements
        this.loadingContainer = document.getElementById('loadingContainer');
        this.resultsSection = document.getElementById('resultsSection');
        this.healthStatus = document.getElementById('healthStatus');
        this.severityLevel = document.getElementById('severityLevel');
        this.severityScore = document.getElementById('severityScore');
        this.diseasesList = document.getElementById('diseasesList');
        this.pestsList = document.getElementById('pestsList');
        this.abioticList = document.getElementById('abioticList');
        this.healthConfidence = document.getElementById('healthConfidence');
        this.healthConfidenceValue = document.getElementById('healthConfidenceValue');
        this.advisorySummary = document.getElementById('advisorySummary');
        this.priorityBadge = document.getElementById('priorityBadge');
        this.priorityText = document.getElementById('priorityText');
        this.chemicalTreatments = document.getElementById('chemicalTreatments');
        this.biologicalTreatments = document.getElementById('biologicalTreatments');
        this.culturalTreatments = document.getElementById('culturalTreatments');
        this.expertAlert = document.getElementById('expertAlert');
        this.preventionList = document.getElementById('preventionList');
        
        // Store last results for report generation
        this.lastPrediction = null;
        this.lastAdvisory = null;
        this.confidenceChart = null;
    }

    attachEventListeners() {
        // File upload
        this.uploadArea.addEventListener('click', () => this.fileInput.click());
        this.selectFileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.fileInput.click();
        });
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        this.uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.uploadArea.addEventListener('drop', (e) => this.handleDrop(e));

        // Remove image
        this.removeImageBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.removeImage();
        });

        // Threshold slider
        this.threshold.addEventListener('input', (e) => {
            this.thresholdValue.textContent = e.target.value;
        });

        // Analyze button
        this.analyzeBtn.addEventListener('click', () => this.analyzeImage());

        // New analysis button
        this.newAnalysisBtn.addEventListener('click', () => this.resetForm());
        
        // Download report button
        this.downloadReportBtn.addEventListener('click', () => this.downloadReport());
    }

    handleDragOver(e) {
        e.preventDefault();
        this.uploadArea.style.borderColor = 'var(--primary-dark)';
        this.uploadArea.style.backgroundColor = 'rgba(74, 144, 226, 0.1)';
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.uploadArea.style.borderColor = 'var(--primary-color)';
        this.uploadArea.style.backgroundColor = 'var(--white)';
    }

    handleDrop(e) {
        e.preventDefault();
        this.uploadArea.style.borderColor = 'var(--primary-color)';
        this.uploadArea.style.backgroundColor = 'var(--white)';

        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].type.startsWith('image/')) {
            this.handleFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.handleFile(file);
        }
    }

    handleFile(file) {
        this.selectedFile = file;

        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            this.previewImage.src = e.target.result;
            this.uploadArea.style.display = 'none';
            this.previewContainer.style.display = 'inline-block';
            this.analyzeBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    removeImage() {
        this.selectedFile = null;
        this.fileInput.value = '';
        this.previewImage.src = '';
        this.uploadArea.style.display = 'block';
        this.previewContainer.style.display = 'none';
        this.analyzeBtn.disabled = true;
    }

    async analyzeImage() {
        if (!this.selectedFile) return;

        // Show loading
        this.loadingContainer.style.display = 'block';
        this.analyzeBtn.disabled = true;

        // Create form data
        const formData = new FormData();
        formData.append('file', this.selectedFile);
        formData.append('crop_type', this.cropType.value);
        formData.append('threshold', this.threshold.value);

        try {
            // Make API call
            const response = await fetch(`${this.apiBaseUrl}/predict-and-advise`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Analysis failed. Please try again.');
            }

            const data = await response.json();
            
            // Display results
            this.displayResults(data);
            
        } catch (error) {
            console.error('Error:', error);
            alert('Error analyzing image: ' + error.message);
        } finally {
            this.loadingContainer.style.display = 'none';
            this.analyzeBtn.disabled = false;
        }
    }

    displayResults(data) {
        const prediction = data.prediction;
        const advisory = data.advisory;
        
        // Store results for report generation
        this.lastPrediction = prediction;
        this.lastAdvisory = advisory;
        
        // Show fallback notice if using fallback predictor
        if (prediction.using_fallback) {
            this.advisorySummary.innerHTML = '<strong>Note:</strong> Using rule-based analysis (trained model not loaded). For more accurate results, train a model using the provided notebooks.';
        } else {
            this.advisorySummary.textContent = advisory.summary;
        }
        
        // Health status
        this.healthStatus.textContent = prediction.health_status.charAt(0).toUpperCase() + prediction.health_status.slice(1);
        this.healthStatus.className = 'health-status ' + prediction.health_status;
        
        // Severity
        this.severityLevel.textContent = prediction.severity_level.charAt(0).toUpperCase() + prediction.severity_level.slice(1);
        this.severityScore.textContent = `(${prediction.severity.toFixed(1)}/3.0)`;
        
        // Diseases
        this.diseasesList.innerHTML = '';
        if (prediction.diseases.length > 0) {
            prediction.diseases.forEach(disease => {
                const tag = document.createElement('span');
                tag.className = 'issue-tag';
                tag.textContent = disease.replace('_', ' ');
                this.diseasesList.appendChild(tag);
            });
        } else {
            this.diseasesList.innerHTML = '<span class="no-issues">No diseases detected</span>';
        }

        // Pests
        this.pestsList.innerHTML = '';
        if (prediction.pests.length > 0) {
            prediction.pests.forEach(pest => {
                const tag = document.createElement('span');
                tag.className = 'issue-tag';
                tag.textContent = pest.replace('_', ' ');
                this.pestsList.appendChild(tag);
            });
        } else {
            this.pestsList.innerHTML = '<span class="no-issues">No pests detected</span>';
        }

        // Abiotic stresses
        this.abioticList.innerHTML = '';
        if (prediction.abiotic_stresses.length > 0) {
            prediction.abiotic_stresses.forEach(stress => {
                const tag = document.createElement('span');
                tag.className = 'issue-tag';
                tag.textContent = stress.replace('_', ' ');
                this.abioticList.appendChild(tag);
            });
        } else {
            this.abioticList.innerHTML = '<span class="no-issues">No abiotic stresses detected</span>';
        }

        // Health confidence
        const healthConf = prediction.confidence.health_status * 100;
        this.healthConfidence.style.width = healthConf + '%';
        this.healthConfidenceValue.textContent = healthConf.toFixed(1) + '%';
        
        // Render Chart.js
        this.renderChart(prediction.confidence);
        
        // Priority
        this.priorityBadge.className = 'priority-badge ' + advisory.priority;
        this.priorityText.textContent = advisory.priority.charAt(0).toUpperCase() + advisory.priority.slice(1) + ' Priority';
        
        // Treatments
        this.chemicalTreatments.innerHTML = '';
        if (advisory.treatments.chemical.length > 0) {
            advisory.treatments.chemical.forEach(treatment => {
                const li = document.createElement('li');
                li.textContent = treatment;
                this.chemicalTreatments.appendChild(li);
            });
        } else {
            this.chemicalTreatments.innerHTML = '<li>No chemical treatments recommended</li>';
        }

        this.biologicalTreatments.innerHTML = '';
        if (advisory.treatments.biological.length > 0) {
            advisory.treatments.biological.forEach(treatment => {
                const li = document.createElement('li');
                li.textContent = treatment;
                this.biologicalTreatments.appendChild(li);
            });
        } else {
            this.biologicalTreatments.innerHTML = '<li>No biological treatments recommended</li>';
        }

        this.culturalTreatments.innerHTML = '';
        if (advisory.treatments.cultural.length > 0) {
            advisory.treatments.cultural.forEach(treatment => {
                const li = document.createElement('li');
                li.textContent = treatment;
                this.culturalTreatments.appendChild(li);
            });
        } else {
            this.culturalTreatments.innerHTML = '<li>No cultural practices recommended</li>';
        }

        // Expert alert
        this.expertAlert.style.display = advisory.expert_needed ? 'flex' : 'none';
        
        // Prevention
        this.preventionList.innerHTML = '';
        advisory.prevention.forEach(prevention => {
            const li = document.createElement('li');
            li.textContent = prevention;
            this.preventionList.appendChild(li);
        });

        // Show results
        this.resultsSection.style.display = 'block';
        
        // Scroll to results
        this.resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    renderChart(confidenceData) {
        const ctx = document.getElementById('confidenceChart').getContext('2d');
        
        // Destroy existing chart if present
        if (this.confidenceChart) {
            this.confidenceChart.destroy();
        }
        
        let labels = [];
        let data = [];
        
        if (confidenceData.health_status) {
            labels.push('Health Status');
            data.push(confidenceData.health_status * 100);
        }
        
        if (confidenceData.diseases) {
            for (let [d, conf] of Object.entries(confidenceData.diseases)) {
                labels.push('Disease: ' + d.replace('_', ' '));
                data.push(conf * 100);
            }
        }
        if (confidenceData.pests) {
            for (let [p, conf] of Object.entries(confidenceData.pests)) {
                labels.push('Pest: ' + p.replace('_', ' '));
                data.push(conf * 100);
            }
        }
        let abioticKey = confidenceData.abiotic_stresses ? 'abiotic_stresses' : 'abiotic';
        if (confidenceData[abioticKey]) {
            for (let [a, conf] of Object.entries(confidenceData[abioticKey])) {
                labels.push('Stress: ' + a.replace('_', ' '));
                data.push(conf * 100);
            }
        }
        
        // Generate colors for pie chart slices
        const backgroundColors = [
            'rgba(76, 175, 80, 0.7)',  // Green
            'rgba(244, 67, 54, 0.7)',  // Red
            'rgba(33, 150, 243, 0.7)', // Blue
            'rgba(255, 152, 0, 0.7)',  // Orange
            'rgba(156, 39, 176, 0.7)', // Purple
            'rgba(0, 188, 212, 0.7)'   // Cyan
        ];
        
        const borderColors = backgroundColors.map(color => color.replace('0.7', '1'));
        
        this.confidenceChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Confidence (%)',
                    data: data,
                    backgroundColor: backgroundColors.slice(0, data.length),
                    borderColor: borderColors.slice(0, data.length),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
    }
    
    async downloadReport() {
        if (!this.lastPrediction || !this.lastAdvisory) {
            alert('No analysis results available. Please analyze an image first.');
            return;
        }
        
        try {
            // Create a dynamic form to submit the POST request
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `${this.apiBaseUrl}/download-report`;
            form.target = '_blank'; // Optional: open in new tab if browser blocks same-tab downloads
            
            const predInput = document.createElement('input');
            predInput.type = 'hidden';
            predInput.name = 'prediction';
            predInput.value = JSON.stringify(this.lastPrediction);
            
            const advInput = document.createElement('input');
            advInput.type = 'hidden';
            advInput.name = 'advisory';
            advInput.value = JSON.stringify(this.lastAdvisory);
            
            const cropInput = document.createElement('input');
            cropInput.type = 'hidden';
            cropInput.name = 'crop_type';
            cropInput.value = this.cropType.value || 'unknown';
            
            form.appendChild(predInput);
            form.appendChild(advInput);
            form.appendChild(cropInput);
            
            document.body.appendChild(form);
            form.submit();
            
            // Clean up
            setTimeout(() => {
                document.body.removeChild(form);
            }, 1000);
            
        } catch (error) {
            console.error('Error:', error);
            alert('Error downloading report: ' + error.message);
        }
    }

    resetForm() {
        this.removeImage();
        this.cropType.value = 'unknown';
        this.threshold.value = 0.5;
        this.thresholdValue.textContent = '0.5';
        this.resultsSection.style.display = 'none';
        this.uploadArea.scrollIntoView({ behavior: 'smooth' });
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AgriGuardApp();
});
