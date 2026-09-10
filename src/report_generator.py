"""
PDF Report Generator Module
Generates PDF reports for plant health analysis results
"""

from datetime import datetime
from typing import Dict, Optional
import io
import matplotlib
matplotlib.use('Agg')


class ReportGenerator:
    """Generates PDF reports for plant health analysis"""
    
    def __init__(self):
        """Initialize report generator"""
        pass
    
    def generate_report(self, prediction: Dict, advisory: Dict, 
                       crop_type: str, image_data: Optional[bytes] = None) -> bytes:
        """
        Generate PDF report
        
        Args:
            prediction: Prediction results
            advisory: Advisory recommendations
            crop_type: Type of plant/tree
            image_data: Optional image data bytes
        
        Returns:
            PDF as bytes
        """
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
        except ImportError:
            # Fallback: generate text report if reportlab not available
            return self._generate_text_report(prediction, advisory, crop_type)
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2E7D32'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1B5E20'),
            spaceAfter=12,
            spaceBefore=20
        )
        normal_style = styles['Normal']
        normal_style.fontSize = 11
        
        # Content
        story = []
        
        # Title
        story.append(Paragraph("AgriGuard AI - Plant Health Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Date and Crop Type
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        story.append(Paragraph(f"<b>Date:</b> {date_str}", normal_style))
        story.append(Paragraph(f"<b>Plant/Tree Type:</b> {crop_type.title()}", normal_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Health Status
        story.append(Paragraph("Health Status", heading_style))
        health_data = [
            ['Status', prediction['health_status'].title()],
            ['Severity Level', prediction['severity_level'].title()],
            ['Severity Score', f"{prediction['severity']:.2f}/3.0"]
        ]
        health_table = Table(health_data, colWidths=[2*inch, 2*inch])
        health_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F5E9')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#F1F8E9')),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(health_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Detected Issues
        story.append(Paragraph("Detected Issues", heading_style))
        
        if prediction['diseases']:
            story.append(Paragraph("<b>Diseases:</b>", normal_style))
            for disease in prediction['diseases']:
                story.append(Paragraph(f"• {disease.replace('_', ' ').title()}", normal_style))
        else:
            story.append(Paragraph("No diseases detected", normal_style))
        
        story.append(Spacer(1, 0.1*inch))
        
        if prediction['pests']:
            story.append(Paragraph("<b>Pests:</b>", normal_style))
            for pest in prediction['pests']:
                story.append(Paragraph(f"• {pest.replace('_', ' ').title()}", normal_style))
        else:
            story.append(Paragraph("No pests detected", normal_style))
        
        story.append(Spacer(1, 0.1*inch))
        
        if prediction['abiotic_stresses']:
            story.append(Paragraph("<b>Abiotic Stresses:</b>", normal_style))
            for stress in prediction['abiotic_stresses']:
                story.append(Paragraph(f"• {stress.replace('_', ' ').title()}", normal_style))
        else:
            story.append(Paragraph("No abiotic stresses detected", normal_style))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Advisory
        story.append(Paragraph("Treatment Recommendations", heading_style))
        story.append(Paragraph(f"<b>Priority:</b> {advisory['priority'].title()}", normal_style))
        story.append(Spacer(1, 0.1*inch))
        
        if advisory.get('treatments', {}).get('chemical'):
            story.append(Paragraph("<b>Chemical Treatments:</b>", normal_style))
            for treatment in advisory['treatments']['chemical']:
                story.append(Paragraph(f"• {treatment}", normal_style))
            story.append(Spacer(1, 0.1*inch))
        
        if advisory.get('treatments', {}).get('biological'):
            story.append(Paragraph("<b>Biological Treatments:</b>", normal_style))
            for treatment in advisory['treatments']['biological']:
                story.append(Paragraph(f"• {treatment}", normal_style))
            story.append(Spacer(1, 0.1*inch))
        
        if advisory.get('treatments', {}).get('cultural'):
            story.append(Paragraph("<b>Cultural Practices:</b>", normal_style))
            for treatment in advisory['treatments']['cultural']:
                story.append(Paragraph(f"• {treatment}", normal_style))
            story.append(Spacer(1, 0.1*inch))
        
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Data Analysis Section
        story.append(Paragraph("Data Analysis & Confidence Scores", heading_style))
        
        try:
            import matplotlib.pyplot as plt
            
            # Prepare data for chart
            labels = []
            scores = []
            
            # Health status confidence
            if 'health_status' in prediction.get('confidence', {}):
                labels.append(prediction['health_status'].title())
                scores.append(prediction['confidence']['health_status'] * 100)
                
            # Disease confidences
            if 'diseases' in prediction.get('confidence', {}) and isinstance(prediction['confidence']['diseases'], dict):
                for d, conf in prediction['confidence']['diseases'].items():
                    labels.append(f"Disease: {d.replace('_', ' ').title()}")
                    scores.append(conf * 100)
            
            # Pests confidences
            if 'pests' in prediction.get('confidence', {}) and isinstance(prediction['confidence']['pests'], dict):
                for p, conf in prediction['confidence']['pests'].items():
                    labels.append(f"Pest: {p.replace('_', ' ').title()}")
                    scores.append(conf * 100)
                    
            # Abiotic confidences
            # Fallback predictor uses 'abiotic', trained model might use 'abiotic_stresses'
            abiotic_key = 'abiotic_stresses' if 'abiotic_stresses' in prediction.get('confidence', {}) else 'abiotic'
            if abiotic_key in prediction.get('confidence', {}) and isinstance(prediction['confidence'][abiotic_key], dict):
                for a, conf in prediction['confidence'][abiotic_key].items():
                    labels.append(f"Stress: {a.replace('_', ' ').title()}")
                    scores.append(conf * 100)
                    
            if labels and scores:
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.pie(scores, labels=labels, autopct='%1.1f%%', startangle=140, colors=['#4CAF50', '#F44336', '#2196F3', '#FF9800', '#9C27B0', '#00BCD4'])
                ax.set_title('Prediction Confidence Analysis')
                ax.axis('equal')
                fig.tight_layout()
                
                # Save to buffer
                img_buf = io.BytesIO()
                fig.savefig(img_buf, format='png', dpi=150)
                img_buf.seek(0)
                plt.close(fig)
                
                # Add to story
                chart_image = Image(img_buf, width=5*inch, height=3.3*inch)
                story.append(chart_image)
                story.append(Spacer(1, 0.2*inch))
        except Exception as e:
            story.append(Paragraph(f"Could not generate charts: {str(e)}", normal_style))
        
        # Prevention
        story.append(Paragraph("Preventive Measures", heading_style))
        for prevention in advisory.get('prevention', []):
            story.append(Paragraph(f"• {prevention}", normal_style))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Expert Alert
        if advisory.get('expert_needed'):
            story.append(Paragraph("⚠ Expert Consultation Recommended", 
                                 ParagraphStyle('Alert', parent=normal_style,
                                              textColor=colors.red,
                                              fontSize=12,
                                              fontName='Helvetica-Bold')))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("Generated by AgriGuard AI - Full-Plant Health Assessment System", 
                             ParagraphStyle('Footer', parent=normal_style,
                                          fontSize=9,
                                          textColor=colors.grey,
                                          alignment=TA_CENTER)))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _generate_text_report(self, prediction: Dict, advisory: Dict, crop_type: str) -> bytes:
        """Generate text report as fallback"""
        text = f"""
AgriGuard AI - Plant Health Report
{'='*50}
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Plant/Tree Type: {crop_type.title()}

HEALTH STATUS
{'-'*30}
Status: {prediction['health_status'].title()}
Severity Level: {prediction['severity_level'].title()}
Severity Score: {prediction['severity']:.2f}/3.0

DETECTED ISSUES
{'-'*30}
"""
        if prediction['diseases']:
            text += "Diseases:\n"
            for disease in prediction['diseases']:
                text += f"  • {disease.replace('_', ' ').title()}\n"
        else:
            text += "No diseases detected\n"
        
        text += "\n"
        if prediction['pests']:
            text += "Pests:\n"
            for pest in prediction['pests']:
                text += f"  • {pest.replace('_', ' ').title()}\n"
        else:
            text += "No pests detected\n"
        
        text += "\n"
        if prediction['abiotic_stresses']:
            text += "Abiotic Stresses:\n"
            for stress in prediction['abiotic_stresses']:
                text += f"  • {stress.replace('_', ' ').title()}\n"
        else:
            text += "No abiotic stresses detected\n"
        
        text += f"""
TREATMENT RECOMMENDATIONS
{'-'*30}
Priority: {advisory['priority'].title()}
"""
        if advisory.get('treatments', {}).get('chemical'):
            text += "\nChemical Treatments:\n"
            for treatment in advisory['treatments']['chemical']:
                text += f"  • {treatment}\n"
        
        if advisory.get('treatments', {}).get('biological'):
            text += "\nBiological Treatments:\n"
            for treatment in advisory['treatments']['biological']:
                text += f"  • {treatment}\n"
        
        if advisory.get('treatments', {}).get('cultural'):
            text += "\nCultural Practices:\n"
            for treatment in advisory['treatments']['cultural']:
                text += f"  • {treatment}\n"
        
        text += f"""
DATA ANALYSIS & CONFIDENCE
{'-'*30}
"""
        if 'confidence' in prediction:
            if 'health_status' in prediction['confidence']:
                text += f"Health Status: {prediction['confidence']['health_status']*100:.1f}%\n"
            
            if 'diseases' in prediction['confidence'] and isinstance(prediction['confidence']['diseases'], dict):
                for d, conf in prediction['confidence']['diseases'].items():
                    text += f"Disease - {d.replace('_', ' ').title()}: {conf*100:.1f}%\n"
                    
            if 'pests' in prediction['confidence'] and isinstance(prediction['confidence']['pests'], dict):
                for p, conf in prediction['confidence']['pests'].items():
                    text += f"Pest - {p.replace('_', ' ').title()}: {conf*100:.1f}%\n"
                    
            abiotic_key = 'abiotic_stresses' if 'abiotic_stresses' in prediction['confidence'] else 'abiotic'
            if abiotic_key in prediction['confidence'] and isinstance(prediction['confidence'][abiotic_key], dict):
                for a, conf in prediction['confidence'][abiotic_key].items():
                    text += f"Stress - {a.replace('_', ' ').title()}: {conf*100:.1f}%\n"
        else:
            text += "No confidence scores available.\n"
            
        text += f"""
PREVENTIVE MEASURES
{'-'*30}
"""
        for prevention in advisory.get('prevention', []):
            text += f"• {prevention}\n"
        
        if advisory.get('expert_needed'):
            text += "\n⚠ Expert Consultation Recommended\n"
        
        text += f"\n{'='*50}\nGenerated by AgriGuard AI\n"
        
        return text.encode('utf-8')


def create_report_generator() -> ReportGenerator:
    """Factory function to create report generator"""
    return ReportGenerator()


if __name__ == "__main__":
    print("Report generator module loaded")
