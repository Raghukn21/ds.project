"""
Advisory Module for AgriGuard AI
Generates treatment recommendations and preventive measures
"""

from typing import Dict, List, Optional


class AdvisoryEngine:
    """
    Decision and advisory engine for plant health recommendations
    """
    
    def __init__(self):
        # Disease treatment database
        self.disease_treatments = {
            'early_blight': {
                'chemical': [
                    "Apply chlorothalonil or copper-based fungicide as per label instructions.",
                    "Use mancozeb or chlorothalonil every 7-10 days during wet conditions."
                ],
                'biological': [
                    "Apply Bacillus subtilis or Trichoderma-based biofungicides.",
                    "Use neem oil spray as a preventive measure."
                ],
                'cultural': [
                    "Remove and destroy infected leaves immediately.",
                    "Improve air circulation by proper plant spacing.",
                    "Avoid overhead irrigation; water at the base of plants.",
                    "Practice crop rotation with non-host crops.",
                    "Ensure proper drainage to reduce humidity."
                ]
            },
            'late_blight': {
                'chemical': [
                    "Apply specific late-blight fungicides (e.g., mefenoxam, copper) immediately upon detection.",
                    "Use protectant fungicides like chlorothalonil before disease onset."
                ],
                'biological': [
                    "Apply copper-based fungicides as a safer alternative."
                ],
                'cultural': [
                    "Remove and destroy heavily infected plants to prevent spread.",
                    "Improve drainage and reduce leaf wetness.",
                    "Avoid working with plants when wet.",
                    "Use resistant varieties if available."
                ]
            },
            'powdery_mildew': {
                'chemical': [
                    "Apply sulfur-based fungicides or neem oil.",
                    "Use potassium bicarbonate sprays."
                ],
                'biological': [
                    "Apply milk spray (1:10 dilution) weekly.",
                    "Use neem oil or garlic spray."
                ],
                'cultural': [
                    "Improve air circulation around plants.",
                    "Avoid overhead irrigation.",
                    "Remove infected plant parts.",
                    "Plant in full sun to reduce humidity."
                ]
            },
            'leaf_spot': {
                'chemical': [
                    "Apply copper fungicide or chlorothalonil.",
                    "Use mancozeb for severe infections."
                ],
                'biological': [
                    "Apply compost tea or Bacillus-based biofungicides."
                ],
                'cultural': [
                    "Remove and destroy affected leaves.",
                    "Avoid wetting foliage when watering.",
                    "Improve air circulation.",
                    "Rotate crops annually."
                ]
            },
            'bacterial_spot': {
                'chemical': [
                    "Apply copper-based bactericides.",
                    "Use streptomycin where permitted."
                ],
                'biological': [
                    "Apply Bacillus subtilis products."
                ],
                'cultural': [
                    "Use disease-free seeds and transplants.",
                    "Avoid working with plants when wet.",
                    "Remove crop debris after harvest.",
                    "Practice crop rotation."
                ]
            },
            'viral_infection': {
                'chemical': [
                    "No chemical cure available. Focus on prevention."
                ],
                'biological': [
                    "Use reflective mulches to deter insect vectors."
                ],
                'cultural': [
                    "Remove and destroy infected plants immediately.",
                    "Control insect vectors (aphids, whiteflies).",
                    "Use virus-free seeds and plants.",
                    "Disinfect tools regularly."
                ]
            },
            'fungal_infection': {
                'chemical': [
                    "Apply broad-spectrum fungicides based on specific fungus.",
                    "Use copper or sulfur-based treatments."
                ],
                'biological': [
                    "Apply Trichoderma-based biofungicides.",
                    "Use neem oil spray."
                ],
                'cultural': [
                    "Improve air circulation and drainage.",
                    "Remove infected plant material.",
                    "Avoid overhead irrigation.",
                    "Practice crop rotation."
                ]
            }
        }
        
        # Pest treatment database
        self.pest_treatments = {
            'aphids': {
                'chemical': [
                    "Apply insecticidal soap or neem oil.",
                    "Use pyrethrin-based insecticides for severe infestations."
                ],
                'biological': [
                    "Introduce ladybugs or lacewings.",
                    "Release parasitic wasps (Aphidius).",
                    "Spray with neem oil or insecticidal soap."
                ],
                'cultural': [
                    "Spray plants with strong water stream to dislodge aphids.",
                    "Remove heavily infested leaves.",
                    "Use reflective mulches to deter aphids.",
                    "Avoid over-fertilizing with nitrogen."
                ]
            },
            'whiteflies': {
                'chemical': [
                    "Apply insecticidal soap or neem oil.",
                    "Use systemic insecticides for severe cases."
                ],
                'biological': [
                    "Release Encarsia formosa parasitic wasps.",
                    "Use yellow sticky traps to monitor and reduce population."
                ],
                'cultural': [
                    "Remove infested leaves.",
                    "Use yellow sticky traps.",
                    "Avoid planting near infested areas.",
                    "Maintain good air circulation."
                ]
            },
            'thrips': {
                'chemical': [
                    "Apply spinosad or insecticidal soap.",
                    "Use neem oil for lighter infestations."
                ],
                'biological': [
                    "Release predatory mites (Amblyseius).",
                    "Use blue sticky traps."
                ],
                'cultural': [
                    "Remove weeds around plants.",
                    "Use blue sticky traps.",
                    "Avoid over-fertilizing.",
                    "Keep plants well-watered."
                ]
            },
            'spider_mites': {
                'chemical': [
                    "Apply miticides specifically for spider mites.",
                    "Use insecticidal soap or neem oil."
                ],
                'biological': [
                    "Release predatory mites (Phytoseiulus).",
                    "Spray with neem oil."
                ],
                'cultural': [
                    "Increase humidity around plants (mites dislike humidity).",
                    "Spray plants with water to dislodge mites.",
                    "Remove heavily infested leaves.",
                    "Avoid broad-spectrum insecticides that kill predators."
                ]
            },
            'caterpillars': {
                'chemical': [
                    "Apply Bt (Bacillus thuringiensis) spray.",
                    "Use spinosad for larger caterpillars."
                ],
                'biological': [
                    "Hand-pick caterpillars when feasible.",
                    "Introduce natural predators like birds."
                ],
                'cultural': [
                    "Remove caterpillars by hand.",
                    "Use row covers to prevent egg-laying.",
                    "Remove egg clusters from leaves.",
                    "Keep garden area clean of debris."
                ]
            }
        }
        
        # Abiotic stress treatments
        self.abiotic_treatments = {
            'nutrient_deficiency': {
                'recommendations': [
                    "Conduct soil test to identify specific nutrient deficiencies.",
                    "Apply balanced NPK fertilizer based on soil test results.",
                    "For nitrogen deficiency: apply blood meal or fish emulsion.",
                    "For phosphorus deficiency: add bone meal or rock phosphate.",
                    "For potassium deficiency: use kelp meal or greensand.",
                    "For micronutrient deficiencies: apply chelated micronutrients.",
                    "Adjust soil pH if needed (most nutrients available at pH 6.0-7.0)."
                ]
            },
            'water_stress': {
                'recommendations': [
                    "Establish consistent watering schedule.",
                    "Water deeply but infrequently to encourage deep root growth.",
                    "Mulch around plants to retain moisture.",
                    "Water in early morning to reduce evaporation.",
                    "Consider drip irrigation for efficient water use.",
                    "Check soil moisture before watering."
                ]
            },
            'heat_stress': {
                'recommendations': [
                    "Provide shade during hottest part of day.",
                    "Increase watering frequency during heat waves.",
                    "Mulch heavily to keep soil cool.",
                    "Ensure good air circulation.",
                    "Avoid fertilizing during extreme heat.",
                    "Consider heat-tolerant varieties for future planting."
                ]
            },
            'salt_stress': {
                'recommendations': [
                    "Flush soil with fresh water to leach excess salts.",
                    "Improve drainage to prevent salt accumulation.",
                    "Use organic matter to improve soil structure.",
                    "Choose salt-tolerant varieties.",
                    "Avoid over-fertilizing.",
                    "Test irrigation water for salt content."
                ]
            },
            'light_stress': {
                'recommendations': [
                    "Ensure plants receive adequate sunlight based on species requirements.",
                    "Prune surrounding plants that may be shading.",
                    "Consider supplemental grow lights for indoor plants.",
                    "Move potted plants to better light conditions.",
                    "Avoid sudden changes in light exposure."
                ]
            }
        }
        
        # General preventive measures
        self.general_prevention = [
            "Practice crop rotation with non-host crops annually.",
            "Use disease-resistant varieties when available.",
            "Maintain proper plant spacing for good air circulation.",
            "Keep garden area clean of debris and weeds.",
            "Disinfect tools regularly to prevent disease spread.",
            "Monitor plants regularly for early signs of problems.",
            "Use clean, disease-free soil and planting material.",
            "Avoid working with plants when they are wet.",
            "Water at the base of plants, not from above.",
            "Encourage beneficial insects and biodiversity."
        ]
    
    def generate_advice(
        self,
        prediction: Dict,
        crop_type: str = 'unknown',
        environment: Optional[Dict] = None
    ) -> Dict:
        """
        Generate comprehensive advisory based on model predictions
        
        Args:
            prediction: Dictionary with model predictions (from inference module)
            crop_type: Type of crop (e.g., 'tomato', 'chili', 'cotton')
            environment: Optional environment data (temp, humidity, soil_moisture)
        
        Returns:
            Dictionary with advisory information
        """
        advice = {
            'summary': '',
            'priority': self._determine_priority(prediction),
            'treatments': {
                'chemical': [],
                'biological': [],
                'cultural': []
            },
            'prevention': [],
            'expert_needed': self._determine_expert_need(prediction),
            'environment_considerations': []
        }
        
        # Add disease treatments
        for disease in prediction.get('diseases', []):
            if disease in self.disease_treatments:
                treatments = self.disease_treatments[disease]
                advice['treatments']['chemical'].extend(treatments['chemical'])
                advice['treatments']['biological'].extend(treatments['biological'])
                advice['treatments']['cultural'].extend(treatments['cultural'])
        
        # Add pest treatments
        for pest in prediction.get('pests', []):
            if pest in self.pest_treatments:
                treatments = self.pest_treatments[pest]
                advice['treatments']['chemical'].extend(treatments['chemical'])
                advice['treatments']['biological'].extend(treatments['biological'])
                advice['treatments']['cultural'].extend(treatments['cultural'])
        
        # Add abiotic stress treatments
        for abiotic in prediction.get('abiotic_stresses', []):
            if abiotic in self.abiotic_treatments:
                advice['treatments']['cultural'].extend(
                    self.abiotic_treatments[abiotic]['recommendations']
                )
        
        # Add general prevention
        advice['prevention'] = self.general_prevention.copy()
        
        # Add crop-specific prevention if available
        crop_specific = self._get_crop_specific_prevention(crop_type)
        if crop_specific:
            advice['prevention'].extend(crop_specific)
        
        # Add environment-based considerations
        if environment:
            env_considerations = self._get_environment_considerations(environment, prediction)
            advice['environment_considerations'] = env_considerations
        
        # Generate summary
        advice['summary'] = self._generate_summary(prediction, crop_type)
        
        # Remove duplicates from treatment lists
        for key in advice['treatments']:
            advice['treatments'][key] = list(dict.fromkeys(advice['treatments'][key]))
        
        return advice
    
    def _determine_priority(self, prediction: Dict) -> str:
        """Determine priority level based on predictions"""
        severity = prediction.get('severity', 0)
        num_issues = (
            len(prediction.get('diseases', [])) +
            len(prediction.get('pests', [])) +
            len(prediction.get('abiotic_stresses', []))
        )
        
        if severity >= 2.5 or num_issues >= 3:
            return 'urgent'
        elif severity >= 1.5 or num_issues >= 2:
            return 'high'
        elif severity >= 0.5 or num_issues >= 1:
            return 'moderate'
        else:
            return 'low'
    
    def _determine_expert_need(self, prediction: Dict) -> bool:
        """Determine if expert consultation is needed"""
        severity = prediction.get('severity', 0)
        num_issues = (
            len(prediction.get('diseases', [])) +
            len(prediction.get('pests', [])) +
            len(prediction.get('abiotic_stresses', []))
        )
        
        # Expert needed for high severity or multiple issues
        if severity >= 2.5 or num_issues >= 3:
            return True
        
        # Expert needed for certain serious diseases
        serious_diseases = ['late_blight', 'viral_infection', 'bacterial_spot']
        for disease in prediction.get('diseases', []):
            if disease in serious_diseases:
                return True
        
        return False
    
    def _get_crop_specific_prevention(self, crop_type: str) -> List[str]:
        """Get crop-specific preventive measures"""
        crop_prevention = {
            'tomato': [
                "Use tomato-specific disease resistant varieties.",
                "Provide support (cages/stakes) to keep fruit off ground.",
                "Prune lower leaves to improve air circulation.",
                "Avoid planting near potatoes (shared diseases)."
            ],
            'chili': [
                "Provide adequate spacing for air circulation.",
                "Avoid excessive nitrogen which promotes disease.",
                "Use mulch to prevent soil splash onto leaves."
            ],
            'cotton': [
                "Monitor for boll weevil and bollworm regularly.",
                    "Use defoliation timing to reduce pest carryover.",
                "Rotate with non-host crops like corn."
            ]
        }
        
        return crop_prevention.get(crop_type.lower(), [])
    
    def _get_environment_considerations(
        self,
        environment: Dict,
        prediction: Dict
    ) -> List[str]:
        """Get environment-based recommendations"""
        considerations = []
        
        temp = environment.get('temperature')
        humidity = environment.get('humidity')
        soil_moisture = environment.get('soil_moisture')
        
        if humidity and humidity > 80:
            considerations.append(
                "High humidity detected - be extra vigilant about fungal diseases. "
                "Improve air circulation and avoid overhead irrigation."
            )
        
        if temp and temp > 35:
            considerations.append(
                "High temperature detected - ensure adequate watering and consider shade. "
                "Heat stress can weaken plants and increase susceptibility to pests."
            )
        
        if soil_moisture and soil_moisture < 30:
            considerations.append(
                "Low soil moisture detected - increase watering frequency. "
                "Water stress can mimic disease symptoms and weaken plants."
            )
        
        # Add disease-specific environment considerations
        if 'late_blight' in prediction.get('diseases', []):
            if humidity and humidity > 90:
                considerations.append(
                    "Late blight thrives in high humidity. Consider preventive fungicide application."
                )
        
        return considerations
    
    def _generate_summary(self, prediction: Dict, crop_type: str) -> str:
        """Generate a summary of the diagnosis"""
        health_status = prediction.get('health_status', 'unknown')
        severity = prediction.get('severity', 0)
        severity_level = prediction.get('severity_level', 'unknown')
        
        diseases = prediction.get('diseases', [])
        pests = prediction.get('pests', [])
        abiotic = prediction.get('abiotic_stresses', [])
        
        all_issues = diseases + pests + abiotic
        
        if health_status == 'healthy':
            return f"The {crop_type} plant appears healthy. Continue regular monitoring and maintain good cultural practices."
        
        if not all_issues:
            return f"The {crop_type} plant shows signs of stress (severity: {severity_level}). Follow the recommended preventive measures."
        
        issues_str = ', '.join(all_issues[:3])  # Limit to top 3 issues
        if len(all_issues) > 3:
            issues_str += f", and {len(all_issues) - 3} other issue(s)"
        
        return (
            f"The {crop_type} plant shows signs of {issues_str} "
            f"with severity level {severity_level} ({severity:.1f}/3.0). "
            f"Follow the recommended treatments and preventive measures."
        )


def create_advisory_engine() -> AdvisoryEngine:
    """Factory function to create advisory engine"""
    return AdvisoryEngine()


if __name__ == "__main__":
    print("Advisory module loaded successfully")
