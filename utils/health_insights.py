# ============================================================
# utils/health_insights.py — Clinical Educational Guidance & Wellness Engine
# ============================================================

from typing import Dict, List, Any, Optional

# ── Disease Educational Metadata ──────────────────────────────
DISEASE_INSIGHTS_CONFIG = {
    'diabetes': {
        'name': 'Diabetes Mellitus',
        'intro': 'Diabetes is a metabolic condition affecting how your body processes blood sugar (glucose). Routine screening and lifestyle management play a decisive role in long-term metabolic health.',
        'high_risk_advice': [
            'Schedule a comprehensive clinical evaluation with a physician, including an HbA1c blood test.',
            'Maintain a daily log of fasting and post-meal blood sugar levels.',
            'Adopt a low-glycaemic nutrition plan rich in soluble fibre, lean proteins, and complex carbohydrates.',
            'Engage in 150 minutes of moderate aerobic activity weekly, such as brisk walking, swimming, or cycling.',
            'Stay alert for symptoms such as excessive thirst, frequent urination, unexplained weight loss, or fatigue.'
        ],
        'mod_risk_advice': [
            'Consult your healthcare provider for periodic blood glucose monitoring.',
            'Minimize intake of refined sugars, sweetened beverages, and ultra-processed carbohydrates.',
            'Incorporate daily 30-minute moderate physical activity to improve insulin sensitivity.',
            'Focus on maintaining a healthy body weight and waist circumference.',
            'Prioritize 7–8 hours of quality sleep to support endocrine regulation.'
        ],
        'low_risk_advice': [
            'Maintain balanced, nutrient-dense nutrition with ample green leafy vegetables and whole grains.',
            'Stay physically active through regular walking, strength exercises, and recreational movement.',
            'Undergo routine annual wellness checkups and standard blood panels.',
            'Maintain optimal hydration throughout the day.'
        ],
        'questions_for_doctor': [
            'Would you recommend an HbA1c test or oral glucose tolerance test (OGTT)?',
            'How frequently should I monitor my blood glucose at home?',
            'What target blood pressure and lipid levels are appropriate for my profile?',
            'Are there specific dietary modifications you recommend based on my metabolic markers?'
        ]
    },

    'heart': {
        'name': 'Heart Disease',
        'intro': 'Cardiovascular disease encompasses conditions affecting the heart and blood vessels. Early identification of arterial and cardiac risk markers enables proactive preventive care.',
        'high_risk_advice': [
            'Seek an immediate clinical consultation with a cardiologist or physician for formal evaluation.',
            'Request specialized diagnostic testing, such as a 12-lead ECG, echocardiogram, or cardiac stress test.',
            'Follow an evidence-based cardiac nutrition plan, such as the Mediterranean or DASH diet.',
            'Avoid tobacco, nicotine products, and secondhand smoke exposure completely.',
            'Strictly monitor daily resting blood pressure and resting heart rate.',
            'Seek emergency medical care immediately if you experience chest pain, radiating arm/jaw discomfort, or acute shortness of breath.'
        ],
        'mod_risk_advice': [
            'Discuss your lipid profile and blood pressure with your primary care provider.',
            'Reduce dietary sodium to under 2,000 mg daily and limit saturated fats.',
            'Engage in doctor-approved cardiovascular exercise, building endurance gradually.',
            'Incorporate stress-reduction practices such as diaphragmatic breathing, meditation, or yoga.',
            'Maintain a regular sleep schedule to support healthy cardiovascular rhythms.'
        ],
        'low_risk_advice': [
            'Continue an active lifestyle with a blend of aerobic and strength conditioning.',
            'Emphasize heart-healthy fats (olive oil, avocados, nuts) and dietary fibre.',
            'Maintain an annual lipid panel and blood pressure evaluation.',
            'Keep alcohol consumption minimal or avoid it altogether.'
        ],
        'questions_for_doctor': [
            'Should I have a lipid subfraction or coronary artery calcium (CAC) scan?',
            'What is my optimal target range for blood pressure and LDL cholesterol?',
            'Are there safe intensity limits for my cardiovascular workouts?',
            'How does my family history influence my cardiovascular monitoring frequency?'
        ]
    },

    'parkinsons': {
        'name': "Parkinson's Disease",
        'intro': "Parkinson's is a progressive neurological condition characterized by movement, balance, and vocal changes. Early neurological assessment supports tailored physical and supportive therapies.",
        'high_risk_advice': [
            'Consult a board-certified neurologist or movement disorder specialist promptly.',
            'Request a comprehensive neurological examination and motor assessment.',
            'Engage in targeted physical and occupational therapy to reinforce gait stability and flexibility.',
            'Incorporate vocal exercises and speech-language therapy if speech volume or clarity is affected.',
            'Ensure your home environment is optimized for safety, balance, and fall prevention.'
        ],
        'mod_risk_advice': [
            'Schedule a baseline neurological checkup to evaluate any subtle motor or sensory changes.',
            'Engage in regular balance exercises such as Tai Chi, gentle dance, or tandem walking.',
            'Track any episodic tremors, stiffness, or changes in handwriting or vocal pitch.',
            'Maintain an active social and cognitive routine to nurture neural plasticity.'
        ],
        'low_risk_advice': [
            'Stay physically and cognitively active through reading, learning new skills, and puzzles.',
            'Maintain regular aerobic physical activity to promote general neurovascular health.',
            'Adopt an antioxidant-rich diet with berries, leafy vegetables, and omega-3 fatty acids.'
        ],
        'questions_for_doctor': [
            'What diagnostic examinations are recommended to assess neurological function?',
            'What signs or symptoms should I watch for in everyday motor coordination?',
            'Are there specific physical therapy or balance regimens recommended for me?'
        ]
    },

    'kidney': {
        'name': 'Kidney Disease',
        'intro': 'Chronic kidney disease involves progressive impairment in the renal filtration of metabolic wastes and excess fluids. Careful monitoring of creatinine, blood pressure, and hydration is vital.',
        'high_risk_advice': [
            'Schedule an urgent consultation with a nephrologist for formal renal evaluation.',
            'Obtain comprehensive renal function tests, including serum creatinine, eGFR, and urine microalbumin.',
            'Strictly manage blood pressure to protect delicate glomerular filtration structures.',
            'Consult a renal dietitian regarding protein intake, sodium restrictions, and phosphorus/potassium management.',
            'Avoid over-the-counter NSAIDs (such as ibuprofen and naproxen) which can cause acute renal stress.'
        ],
        'mod_risk_advice': [
            'Review kidney markers (creatinine and BUN) with your primary physician.',
            'Maintain steady daily hydration unless medically restricted by your doctor.',
            'Limit dietary sodium to under 2,000 mg per day and reduce processed foods.',
            'Control blood sugar and blood pressure within target clinical ranges.'
        ],
        'low_risk_advice': [
            'Stay well-hydrated throughout the day with clean water.',
            'Maintain a balanced diet moderate in sodium and high in whole foods.',
            'Undergo standard annual metabolic and urine panels during routine checkups.'
        ],
        'questions_for_doctor': [
            'What is my calculated estimated glomerular filtration rate (eGFR)?',
            'Are any of my current medications or supplements taxing on kidney function?',
            'What specific dietary precautions should I observe regarding sodium or protein?'
        ]
    },

    'liver': {
        'name': 'Liver Disease',
        'intro': 'The liver conducts hundreds of essential metabolic, detoxifying, and protein-synthesizing functions. Hepatic screening evaluates enzyme markers that reflect liver cell integrity.',
        'high_risk_advice': [
            'Arrange a clinical evaluation with a gastroenterologist or hepatologist.',
            'Undergo comprehensive liver function testing (LFTs) and abdominal ultrasound imaging.',
            'Completely abstain from alcohol consumption to prevent cellular stress.',
            'Review all medications, over-the-counter drugs, and herbal supplements with your physician.',
            'Adopt an anti-inflammatory, liver-protective diet low in added sugars and saturated fats.'
        ],
        'mod_risk_advice': [
            'Consult your physician to investigate elevated liver enzymes (ALT, AST, ALP).',
            'Eliminate or substantially reduce alcoholic beverages.',
            'Work towards gradual, sustainable weight management if overweight or fatty liver is suspected.',
            'Ensure up-to-date vaccinations for Hepatitis A and Hepatitis B.'
        ],
        'low_risk_advice': [
            'Maintain a nutrient-rich diet rich in cruciferous vegetables, garlic, and citrus fruits.',
            'Limit alcohol intake and avoid unnecessary medications or high-dose acetaminophen.',
            'Engage in regular physical activity to support metabolic and liver health.'
        ],
        'questions_for_doctor': [
            'Would you recommend an abdominal ultrasound or FibroScan to evaluate liver texture?',
            'What could be causing variations in my liver enzyme levels?',
            'Are my current supplements or medications safe for my liver?'
        ]
    },

    'lung_cancer': {
        'name': 'Lung Cancer',
        'intro': 'Pulmonary health screening evaluates respiratory symptoms and risk factors. Early radiological screening in individuals with significant exposure history dramatically improves clinical outcomes.',
        'high_risk_advice': [
            'Seek an urgent pulmonary or oncology consultation for definitive clinical assessment.',
            'Discuss eligibility for a Low-Dose CT (LDCT) scan of the chest.',
            'If you smoke, seek professional smoking cessation support and nicotine-replacement therapy immediately.',
            'Avoid all exposure to secondhand smoke, radon, industrial fumes, and particulate matter.',
            'Report any persistent cough, hemoptysis (coughing blood), chest pain, or unexplained weight loss immediately.'
        ],
        'mod_risk_advice': [
            'Schedule a respiratory assessment with your physician to evaluate ongoing symptoms.',
            'Begin a structured smoking cessation plan immediately if currently using tobacco.',
            'Improve indoor air quality using HEPA filtration and adequate ventilation.',
            'Maintain a symptom journal detailing any shortness of breath or cough frequency.'
        ],
        'low_risk_advice': [
            'Never initiate smoking, and maintain clean indoor environments.',
            'Engage in cardiovascular physical activities that expand lung capacity.',
            'Protect respiratory health during episodes of high outdoor air pollution.'
        ],
        'questions_for_doctor': [
            'Do I meet the criteria for annual Low-Dose CT (LDCT) lung cancer screening?',
            'What diagnostic tests can help investigate my persistent respiratory symptoms?',
            'What professional smoking cessation resources are available to me?'
        ]
    },

    'hypertension': {
        'name': 'Hypertension',
        'intro': 'High blood pressure creates chronic tension within arterial walls, elevating long-term risks for cardiovascular and cerebrovascular events. Proactive lifestyle modifications have proven efficacy.',
        'high_risk_advice': [
            'Consult your physician promptly to evaluate whether antihypertensive medication is indicated.',
            'Measure and record resting blood pressure twice daily (morning and evening).',
            'Adopt the DASH (Dietary Approaches to Stop Hypertension) dietary framework.',
            'Strictly reduce sodium intake to under 1,500 mg daily.',
            'Seek urgent medical attention if systolic BP exceeds 180 mmHg or diastolic exceeds 120 mmHg, especially with headache or visual changes.'
        ],
        'mod_risk_advice': [
            'Discuss lifestyle hypertension interventions with your doctor.',
            'Reduce dietary sodium, canned foods, and processed snacks.',
            'Practice daily 15-minute mindfulness, meditation, or slow resonant breathing.',
            'Engage in 30 minutes of moderate aerobic exercise 5 days per week.'
        ],
        'low_risk_advice': [
            'Maintain a diet rich in potassium (bananas, spinach, sweet potatoes) and low in sodium.',
            'Maintain an active daily movement routine and healthy BMI.',
            'Check resting blood pressure every 3–6 months.'
        ],
        'questions_for_doctor': [
            'Would ambulatory 24-hour blood pressure monitoring be beneficial?',
            'What is my individualized target blood pressure goal?',
            'Could my blood pressure be secondary to other factors like sleep apnea?'
        ]
    },

    'breast_cancer': {
        'name': 'Breast Cancer',
        'intro': 'Breast screening evaluates physical, clinical, and cellular parameters. Regular mammographic screening and clinical examinations remain the gold standard for early detection.',
        'high_risk_advice': [
            'Schedule an immediate consultation with an oncologist, breast specialist, or surgeon.',
            'Undergo dedicated diagnostic breast imaging, including bilateral diagnostic mammography and targeted ultrasound.',
            'Discuss whether a core needle biopsy or breast MRI is warranted based on findings.',
            'Explore genetic counseling (such as BRCA1/BRCA2 analysis) if family history is present.'
        ],
        'mod_risk_advice': [
            'Discuss comprehensive breast screening options with your gynecologist or physician.',
            'Maintain routine clinical breast examinations alongside regular screening mammography.',
            'Familiarize yourself with normal breast tissue texture through regular awareness.',
            'Limit alcohol intake and maintain regular exercise to support hormonal balance.'
        ],
        'low_risk_advice': [
            'Follow age-appropriate standard mammography screening guidelines.',
            'Practice regular breast self-awareness and report any new lumps or skin changes.',
            'Maintain a balanced lifestyle with regular physical activity and optimal body weight.'
        ],
        'questions_for_doctor': [
            'What is the recommended screening schedule and imaging modality for my breast density?',
            'Does my family or personal history indicate a need for genetic counseling or advanced screening?',
            'What symptoms or physical signs warrant immediate clinical evaluation?'
        ]
    }
}


def generate_health_insights(disease_key: str,
                             result: str,
                             risk_level: str,
                             input_data: Dict[str, Any],
                             user_profile: Optional[Any] = None) -> Dict[str, Any]:
    """
    Generates structured, safe, educational health guidance based on
    prediction output, clinical risk level, and user metrics.
    """
    disease_key = disease_key.lower().strip()
    config = DISEASE_INSIGHTS_CONFIG.get(disease_key, DISEASE_INSIGHTS_CONFIG['diabetes'])

    if risk_level == 'High':
        advice_list = config['high_risk_advice']
        status_heading = f"High Risk Assessment for {config['name']}"
        status_tone = 'urgent'
        summary = (
            f"The machine-learning screening algorithm identified elevated risk markers consistent with "
            f"{config['name']}. This is an informational screening indicator, not a definitive diagnosis. "
            f"We strongly recommend scheduling an appointment with a qualified medical professional for clinical assessment."
        )
    elif risk_level == 'Moderate':
        advice_list = config['mod_risk_advice']
        status_heading = f"Moderate Risk Assessment for {config['name']}"
        status_tone = 'warning'
        summary = (
            f"The assessment identified borderline or moderately elevated risk markers for {config['name']}. "
            f"Early lifestyle interventions and discussion with your healthcare provider can often significantly "
            f"mitigate potential progression."
        )
    else:
        advice_list = config['low_risk_advice']
        status_heading = f"Low Risk Assessment for {config['name']}"
        status_tone = 'positive'
        summary = (
            f"The assessment results fall within standard low-risk parameters for {config['name']}. "
            f"Continuing balanced dietary habits, regular physical activity, and scheduled wellness checkups "
            f"supports sustained long-term health."
        )

    # Identify noteworthy parameters from input_data
    noteworthy_markers = _extract_noteworthy_markers(disease_key, input_data)

    return {
        'disease_name': config['name'],
        'status_heading': status_heading,
        'status_tone': status_tone,
        'summary': summary,
        'intro': config['intro'],
        'recommendations': advice_list,
        'questions_for_doctor': config['questions_for_doctor'],
        'noteworthy_markers': noteworthy_markers,
        'disclaimer': (
            "MediScan Pro is an artificial intelligence screening tool developed for educational, academic, "
            "and health-tracking purposes. It does not provide medical diagnosis, treatment plans, or prescriptions. "
            "Always consult a licensed physician or healthcare professional for medical concerns."
        )
    }


def _extract_noteworthy_markers(disease_key: str, input_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Identifies input values that exceed standard reference thresholds."""
    markers = []
    from ml_models.predictor import THRESHOLDS

    thresholds = THRESHOLDS.get(disease_key, {})
    for field, rule in thresholds.items():
        try:
            val = float(input_data.get(field, 0))
            if val >= rule['high']:
                field_label = field.replace('_', ' ').title()
                markers.append({
                    'param': field_label,
                    'value': f"{val}",
                    'threshold': f">= {rule['high']}",
                    'note': 'Elevated relative to screening baseline'
                })
        except (ValueError, TypeError):
            continue

    return markers


def get_personalized_tasks(disease_key: str, risk_level: str) -> List[Dict[str, str]]:
    """Returns curated daily health tasks tailored to the disease and risk assessment."""
    disease_key = disease_key.lower().strip()

    base_tasks = [
        {'text': 'Hydration Goal: Drink 8–10 glasses (2.5L) of water today', 'category': 'hydration'},
        {'text': 'Physical Activity: 30 minutes of brisk walking or light cardio', 'category': 'exercise'},
        {'text': 'Nutrition: Add 2 servings of green vegetables to your meals', 'category': 'nutrition'},
        {'text': 'Rest & Recovery: Maintain 7–8 hours of quality sleep tonight', 'category': 'wellness'},
    ]

    disease_specific = {
        'diabetes': [
            {'text': 'Blood Sugar Check: Log fasting or post-meal glucose level', 'category': 'monitoring'},
            {'text': 'Nutrition: Avoid sugary beverages and refined white flour today', 'category': 'nutrition'}
        ],
        'heart': [
            {'text': 'Cardiovascular Check: Measure resting pulse and morning blood pressure', 'category': 'monitoring'},
            {'text': 'Nutrition: Choose heart-healthy olive oil and reduce sodium intake', 'category': 'nutrition'}
        ],
        'hypertension': [
            {'text': 'BP Log: Record resting blood pressure morning and evening', 'category': 'monitoring'},
            {'text': 'Stress Relief: Complete 10 minutes of deep diaphragmatic breathing', 'category': 'wellness'}
        ],
        'kidney': [
            {'text': 'Hydration Tracking: Keep a measured water bottle by your desk', 'category': 'hydration'},
            {'text': 'Nutrition: Choose fresh home-cooked food to avoid hidden dietary sodium', 'category': 'nutrition'}
        ],
        'liver': [
            {'text': 'Liver Care: Zero alcohol consumption and drink green tea', 'category': 'wellness'},
            {'text': 'Nutrition: Incorporate antioxidant-rich citrus fruits and broccoli', 'category': 'nutrition'}
        ],
        'lung_cancer': [
            {'text': 'Respiratory Health: Practice 5 minutes of deep breathing exercises', 'category': 'wellness'},
            {'text': 'Clean Air: Avoid tobacco smoke, incense, and unventilated areas', 'category': 'wellness'}
        ],
        'parkinsons': [
            {'text': 'Coordination: Practice 15 minutes of gentle balance and stretching exercises', 'category': 'exercise'},
            {'text': 'Cognitive Activity: Read a chapter of a book or solve a puzzle', 'category': 'wellness'}
        ],
        'breast_cancer': [
            {'text': 'Wellness: 20-minute restorative yoga or brisk outdoor walk', 'category': 'exercise'},
            {'text': 'Nutrition: Include flaxseed and antioxidant-rich berries in breakfast', 'category': 'nutrition'}
        ]
    }

    specific = disease_specific.get(disease_key, [])
    # Combine specific first, followed by base
    tasks = specific + base_tasks
    return tasks[:5]
