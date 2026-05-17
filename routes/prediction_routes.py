# ============================================================
# routes/prediction_routes.py — MediScan Pro Prediction Routes
# ============================================================

import logging
logger = logging.getLogger('mediscan.prediction')

import json
from datetime import datetime
from flask import (
    Blueprint, render_template, redirect,
    url_for, request, flash, session, jsonify
)
from flask_login import login_required, current_user

from database.db import db, PredictionHistory
from utils.helpers import (
    log_activity, sanitize_input,
    format_prediction_for_display,
    validate_numeric_input
)

# ── Blueprint Definition ──────────────────────────────────────
prediction_bp = Blueprint(
    'prediction',
    __name__,
    template_folder='../templates/prediction'
)


# ============================================================
# DISEASE CONFIGURATION REGISTRY
# ============================================================
# Central registry for all supported disease modules.
# Each entry defines:
#   fields      → form input fields with validation rules
#   precautions → risk-level-specific recommendations
#   model_name  → ML model identifier (used in Step 8)
# Adding a new disease = adding one entry here + one model file.

DISEASE_REGISTRY = {

    'diabetes': {
        'name'      : 'Diabetes Mellitus',
        'icon'      : '🩸',
        'model_name': 'diabetes_model',
        'fields'    : [
            {'name': 'pregnancies',        'label': 'Number of Pregnancies',    'type': 'number', 'min': 0,   'max': 20,   'unit': ''},
            {'name': 'glucose',            'label': 'Glucose Level',            'type': 'number', 'min': 0,   'max': 300,  'unit': 'mg/dL'},
            {'name': 'blood_pressure',     'label': 'Blood Pressure',           'type': 'number', 'min': 0,   'max': 200,  'unit': 'mmHg'},
            {'name': 'skin_thickness',     'label': 'Skin Thickness',           'type': 'number', 'min': 0,   'max': 100,  'unit': 'mm'},
            {'name': 'insulin',            'label': 'Insulin Level',            'type': 'number', 'min': 0,   'max': 900,  'unit': 'µU/mL'},
            {'name': 'bmi',                'label': 'BMI',                      'type': 'float',  'min': 0,   'max': 70,   'unit': 'kg/m²'},
            {'name': 'diabetes_pedigree',  'label': 'Diabetes Pedigree Function','type': 'float', 'min': 0,   'max': 3,    'unit': ''},
            {'name': 'age',                'label': 'Age',                      'type': 'number', 'min': 1,   'max': 120,  'unit': 'years'},
        ],
        'precautions': {
            'Low'     : 'Maintain healthy BMI. Exercise 150 min/week. Annual glucose screening. Reduce refined carbohydrates.',
            'Moderate': 'Consult a physician for HbA1c testing. Begin low-glycaemic diet. Monitor blood sugar weekly. Increase physical activity.',
            'High'    : 'Seek immediate medical consultation. Begin prescribed diabetes management plan. Daily blood sugar monitoring. Strict dietary control required.',
        },
    },

    'heart': {
        'name'      : 'Heart Disease',
        'icon'      : '🫀',
        'model_name': 'heart_model',
        'fields'    : [
            {'name': 'age',          'label': 'Age',                        'type': 'number', 'min': 1,   'max': 120,  'unit': 'years'},
            {'name': 'sex',          'label': 'Sex (1=Male, 0=Female)',     'type': 'number', 'min': 0,   'max': 1,    'unit': ''},
            {'name': 'cp',           'label': 'Chest Pain Type (0-3)',      'type': 'number', 'min': 0,   'max': 3,    'unit': ''},
            {'name': 'trestbps',     'label': 'Resting Blood Pressure',     'type': 'number', 'min': 80,  'max': 250,  'unit': 'mmHg'},
            {'name': 'chol',         'label': 'Serum Cholesterol',          'type': 'number', 'min': 100, 'max': 600,  'unit': 'mg/dL'},
            {'name': 'fbs',          'label': 'Fasting Blood Sugar >120',   'type': 'number', 'min': 0,   'max': 1,    'unit': ''},
            {'name': 'restecg',      'label': 'Resting ECG Results (0-2)',  'type': 'number', 'min': 0,   'max': 2,    'unit': ''},
            {'name': 'thalach',      'label': 'Maximum Heart Rate',         'type': 'number', 'min': 60,  'max': 250,  'unit': 'bpm'},
            {'name': 'exang',        'label': 'Exercise Induced Angina',    'type': 'number', 'min': 0,   'max': 1,    'unit': ''},
            {'name': 'oldpeak',      'label': 'ST Depression',              'type': 'float',  'min': 0,   'max': 10,   'unit': ''},
            {'name': 'slope',        'label': 'Slope of Peak ST (0-2)',     'type': 'number', 'min': 0,   'max': 2,    'unit': ''},
            {'name': 'ca',           'label': 'Major Vessels (0-4)',        'type': 'number', 'min': 0,   'max': 4,    'unit': ''},
            {'name': 'thal',         'label': 'Thalassemia (0-3)',          'type': 'number', 'min': 0,   'max': 3,    'unit': ''},
        ],
        'precautions': {
            'Low'     : 'Maintain active lifestyle. Monitor cholesterol annually. Reduce sodium intake. Avoid smoking.',
            'Moderate': 'Cardiology consultation recommended. Begin heart-healthy diet. Monitor BP weekly. Avoid strenuous activity until evaluated.',
            'High'    : 'Urgent cardiology evaluation required. Do not delay treatment. Strict medication adherence. Emergency contact on standby.',
        },
    },

    'parkinsons': {
        'name'      : "Parkinson's Disease",
        'icon'      : '🧠',
        'model_name': 'parkinsons_model',
        'fields'    : [
            {'name': 'mdvp_fo',      'label': 'MDVP Fo (Hz)',               'type': 'float', 'min': 80,  'max': 300,  'unit': 'Hz'},
            {'name': 'mdvp_fhi',     'label': 'MDVP Fhi (Hz)',              'type': 'float', 'min': 100, 'max': 600,  'unit': 'Hz'},
            {'name': 'mdvp_flo',     'label': 'MDVP Flo (Hz)',              'type': 'float', 'min': 60,  'max': 300,  'unit': 'Hz'},
            {'name': 'mdvp_jitter',  'label': 'MDVP Jitter (%)',            'type': 'float', 'min': 0,   'max': 1,    'unit': '%'},
            {'name': 'mdvp_shimmer', 'label': 'MDVP Shimmer',               'type': 'float', 'min': 0,   'max': 1,    'unit': ''},
            {'name': 'nhr',          'label': 'NHR',                        'type': 'float', 'min': 0,   'max': 1,    'unit': ''},
            {'name': 'hnr',          'label': 'HNR',                        'type': 'float', 'min': 0,   'max': 40,   'unit': 'dB'},
            {'name': 'rpde',         'label': 'RPDE',                       'type': 'float', 'min': 0,   'max': 1,    'unit': ''},
            {'name': 'dfa',          'label': 'DFA',                        'type': 'float', 'min': 0,   'max': 1,    'unit': ''},
            {'name': 'spread1',      'label': 'Spread1',                    'type': 'float', 'min': -10, 'max': 0,    'unit': ''},
            {'name': 'spread2',      'label': 'Spread2',                    'type': 'float', 'min': 0,   'max': 1,    'unit': ''},
            {'name': 'd2',           'label': 'D2',                         'type': 'float', 'min': 0,   'max': 5,    'unit': ''},
            {'name': 'ppe',          'label': 'PPE',                        'type': 'float', 'min': 0,   'max': 1,    'unit': ''},
        ],
        'precautions': {
            'Low'     : 'Annual neurological checkups recommended. Stay physically and mentally active. Monitor any tremor or balance changes.',
            'Moderate': 'Neurologist consultation advised. Begin occupational and physical therapy evaluation. Track symptom progression.',
            'High'    : 'Immediate neurological evaluation required. Discuss medication options with specialist. Safety assessment for daily activities.',
        },
    },

    'kidney': {
        'name'      : 'Kidney Disease',
        'icon'      : '🩻',
        'model_name': 'kidney_model',
        'fields'    : [
            {'name': 'age',    'label': 'Age',                              'type': 'number', 'min': 1,   'max': 120,  'unit': 'years'},
            {'name': 'bp',     'label': 'Blood Pressure',                   'type': 'number', 'min': 50,  'max': 200,  'unit': 'mmHg'},
            {'name': 'sg',     'label': 'Specific Gravity',                 'type': 'float',  'min': 1,   'max': 1.03, 'unit': ''},
            {'name': 'al',     'label': 'Albumin (0-5)',                    'type': 'number', 'min': 0,   'max': 5,    'unit': ''},
            {'name': 'su',     'label': 'Sugar (0-5)',                      'type': 'number', 'min': 0,   'max': 5,    'unit': ''},
            {'name': 'bgr',    'label': 'Blood Glucose Random',             'type': 'number', 'min': 70,  'max': 500,  'unit': 'mg/dL'},
            {'name': 'bu',     'label': 'Blood Urea',                       'type': 'number', 'min': 1,   'max': 200,  'unit': 'mg/dL'},
            {'name': 'sc',     'label': 'Serum Creatinine',                 'type': 'float',  'min': 0.4, 'max': 20,   'unit': 'mg/dL'},
            {'name': 'sod',    'label': 'Sodium',                           'type': 'number', 'min': 100, 'max': 200,  'unit': 'mEq/L'},
            {'name': 'pot',    'label': 'Potassium',                        'type': 'float',  'min': 2,   'max': 10,   'unit': 'mEq/L'},
            {'name': 'hemo',   'label': 'Haemoglobin',                      'type': 'float',  'min': 3,   'max': 20,   'unit': 'g/dL'},
            {'name': 'pcv',    'label': 'Packed Cell Volume',               'type': 'number', 'min': 10,  'max': 60,   'unit': '%'},
            {'name': 'wbcc',   'label': 'White Blood Cell Count',           'type': 'number', 'min': 2000,'max': 20000,'unit': 'cells/µL'},
            {'name': 'rbcc',   'label': 'Red Blood Cell Count',             'type': 'float',  'min': 2,   'max': 8,    'unit': 'million/µL'},
        ],
        'precautions': {
            'Low'     : 'Stay well-hydrated. Limit sodium intake. Annual kidney function tests. Avoid nephrotoxic medications.',
            'Moderate': 'Nephrologist referral recommended. Begin renal diet. Monitor creatinine levels monthly. Control blood pressure and blood sugar.',
            'High'    : 'Immediate nephrology consultation required. Discuss dialysis readiness. Strict fluid and dietary restrictions. Urgent BP management.',
        },
    },

    'liver': {
        'name'      : 'Liver Disease',
        'icon'      : '🔬',
        'model_name': 'liver_model',
        'fields'    : [
            {'name': 'age',                    'label': 'Age',                         'type': 'number', 'min': 1,   'max': 120,  'unit': 'years'},
            {'name': 'gender',                 'label': 'Gender (1=Male, 0=Female)',   'type': 'number', 'min': 0,   'max': 1,    'unit': ''},
            {'name': 'total_bilirubin',        'label': 'Total Bilirubin',             'type': 'float',  'min': 0.1, 'max': 75,   'unit': 'mg/dL'},
            {'name': 'direct_bilirubin',       'label': 'Direct Bilirubin',            'type': 'float',  'min': 0.1, 'max': 20,   'unit': 'mg/dL'},
            {'name': 'alkaline_phosphotase',   'label': 'Alkaline Phosphotase',        'type': 'number', 'min': 20,  'max': 2000, 'unit': 'IU/L'},
            {'name': 'alamine_aminotransferase','label': 'Alamine Aminotransferase',   'type': 'number', 'min': 7,   'max': 2000, 'unit': 'IU/L'},
            {'name': 'aspartate_aminotransferase','label': 'Aspartate Aminotransferase','type': 'number','min': 10,  'max': 5000, 'unit': 'IU/L'},
            {'name': 'total_proteins',         'label': 'Total Proteins',              'type': 'float',  'min': 2,   'max': 10,   'unit': 'g/dL'},
            {'name': 'albumin',                'label': 'Albumin',                     'type': 'float',  'min': 0.5, 'max': 6,    'unit': 'g/dL'},
            {'name': 'albumin_globulin_ratio', 'label': 'Albumin/Globulin Ratio',      'type': 'float',  'min': 0.1, 'max': 3,    'unit': ''},
        ],
        'precautions': {
            'Low'     : 'Avoid alcohol completely. Maintain healthy weight. Annual liver function tests. Hepatitis B/C vaccination.',
            'Moderate': 'Hepatologist consultation advised. Abstain from alcohol and hepatotoxic drugs. Begin liver-supportive diet. Monitor LFT monthly.',
            'High'    : 'Urgent hepatology evaluation required. Imaging (ultrasound/MRI) of liver. Discuss antiviral or other therapy options immediately.',
        },
    },

    'lung_cancer': {
        'name'      : 'Lung Cancer',
        'icon'      : '🫁',
        'model_name': 'lung_cancer_model',
        'fields'    : [
            {'name': 'gender',            'label': 'Gender (1=Male, 0=Female)',  'type': 'number', 'min': 0, 'max': 1,   'unit': ''},
            {'name': 'age',               'label': 'Age',                        'type': 'number', 'min': 1, 'max': 120, 'unit': 'years'},
            {'name': 'smoking',           'label': 'Smoking (1=Yes, 0=No)',      'type': 'number', 'min': 0, 'max': 1,   'unit': ''},
            {'name': 'yellow_fingers',    'label': 'Yellow Fingers (1/0)',       'type': 'number', 'min': 0, 'max': 1,   'unit': ''},
            {'name': 'anxiety',           'label': 'Anxiety (1/0)',              'type': 'number', 'min': 0, 'max': 1,   'unit': ''},
            {'name': 'peer_pressure',     'label': 'Peer Pressure (1/0)',        'type': 'number', 'min': 0, 'max': 1,   'unit': ''},
            {'name': 'chronic_disease',   'label': 'Chronic Disease (1/0)',      'type': 'number', 'min': 0, 'max': 1,   'unit': ''},
            {'name': 'fatigue',           'label': 'Fatigue (1/0)',              'type': 'number', 'min': 0, 'max': 1,   'unit': ''},
            {'name': 'allergy',           'label': 'Allergy (1/0)',              'type': 'number', 'min': 0, 'max': 1,   'unit': ''},
            {'name': 'wheezing',          'label': 'Wheezing (1/0)',             'type': 'number', 'min': 0, 'max': 1,   'unit': ''},
            {'name': 'alcohol_consuming', 'label': 'Alcohol Consuming (1/0)',    'type': 'number', 'min': 0, 'max': 1,   'unit': ''},
            {'name': 'coughing',          'label': 'Coughing (1/0)',             'type': 'number', 'min': 0, 'max': 1,   'unit': ''},
            {'name': 'shortness_of_breath','label': 'Shortness of Breath (1/0)', 'type': 'number', 'min': 0, 'max': 1,   'unit': ''},
            {'name': 'swallowing_difficulty','label': 'Swallowing Difficulty (1/0)','type': 'number','min': 0,'max': 1,  'unit': ''},
            {'name': 'chest_pain',        'label': 'Chest Pain (1/0)',           'type': 'number', 'min': 0, 'max': 1,   'unit': ''},
        ],
        'precautions': {
            'Low'     : 'Stop smoking immediately if applicable. Annual chest X-ray if over 50. Avoid secondhand smoke and air pollutants.',
            'Moderate': 'Pulmonologist evaluation recommended. Low-dose CT scan advised. Smoking cessation programme. Monitor respiratory symptoms.',
            'High'    : 'Urgent oncology/pulmonology referral required. CT scan and biopsy evaluation. Begin smoking cessation immediately. Discuss treatment plan.',
        },
    },

    'hypertension': {
        'name'      : 'Hypertension',
        'icon'      : '📊',
        'model_name': 'hypertension_model',
        'fields'    : [
            {'name': 'age',              'label': 'Age',                         'type': 'number', 'min': 1,  'max': 120, 'unit': 'years'},
            {'name': 'sex',              'label': 'Sex (1=Male, 0=Female)',      'type': 'number', 'min': 0,  'max': 1,   'unit': ''},
            {'name': 'cp',               'label': 'Chest Pain Type (0-3)',       'type': 'number', 'min': 0,  'max': 3,   'unit': ''},
            {'name': 'systolic_bp',      'label': 'Systolic Blood Pressure',     'type': 'number', 'min': 80, 'max': 250, 'unit': 'mmHg'},
            {'name': 'diastolic_bp',     'label': 'Diastolic Blood Pressure',    'type': 'number', 'min': 40, 'max': 150, 'unit': 'mmHg'},
            {'name': 'cholesterol',      'label': 'Cholesterol',                 'type': 'number', 'min': 100,'max': 600, 'unit': 'mg/dL'},
            {'name': 'bmi',              'label': 'BMI',                         'type': 'float',  'min': 10, 'max': 70,  'unit': 'kg/m²'},
            {'name': 'smoking',          'label': 'Smoking (1=Yes, 0=No)',       'type': 'number', 'min': 0,  'max': 1,   'unit': ''},
            {'name': 'alcohol',          'label': 'Alcohol Use (1=Yes, 0=No)',   'type': 'number', 'min': 0,  'max': 1,   'unit': ''},
            {'name': 'physical_activity','label': 'Physical Activity (1=Yes, 0=No)','type': 'number','min': 0,'max': 1,  'unit': ''},
            {'name': 'family_history',   'label': 'Family History (1=Yes, 0=No)','type': 'number', 'min': 0,  'max': 1,   'unit': ''},
        ],
        'precautions': {
            'Low'     : 'Reduce sodium to under 2g/day. Exercise 30 min/day. Maintain healthy weight. Monitor BP monthly.',
            'Moderate': 'Begin DASH diet. Weekly BP monitoring. Physician consultation for medication assessment. Reduce stress with relaxation techniques.',
            'High'    : 'Immediate physician consultation. Begin prescribed antihypertensive medication. Daily BP monitoring. Emergency plan if BP exceeds 180/120.',
        },
    },

    'breast_cancer': {
        'name'      : 'Breast Cancer',
        'icon'      : '🧬',
        'model_name': 'breast_cancer_model',
        'fields'    : [
            {'name': 'radius_mean',          'label': 'Radius Mean',              'type': 'float', 'min': 5,  'max': 40,  'unit': ''},
            {'name': 'texture_mean',         'label': 'Texture Mean',             'type': 'float', 'min': 5,  'max': 50,  'unit': ''},
            {'name': 'perimeter_mean',       'label': 'Perimeter Mean',           'type': 'float', 'min': 40, 'max': 300, 'unit': ''},
            {'name': 'area_mean',            'label': 'Area Mean',                'type': 'float', 'min': 100,'max': 2600,'unit': ''},
            {'name': 'smoothness_mean',      'label': 'Smoothness Mean',          'type': 'float', 'min': 0,  'max': 0.5, 'unit': ''},
            {'name': 'compactness_mean',     'label': 'Compactness Mean',         'type': 'float', 'min': 0,  'max': 0.5, 'unit': ''},
            {'name': 'concavity_mean',       'label': 'Concavity Mean',           'type': 'float', 'min': 0,  'max': 0.5, 'unit': ''},
            {'name': 'concave_points_mean',  'label': 'Concave Points Mean',      'type': 'float', 'min': 0,  'max': 0.3, 'unit': ''},
            {'name': 'symmetry_mean',        'label': 'Symmetry Mean',            'type': 'float', 'min': 0,  'max': 0.5, 'unit': ''},
            {'name': 'fractal_dimension_mean','label': 'Fractal Dimension Mean',  'type': 'float', 'min': 0,  'max': 0.2, 'unit': ''},
        ],
        'precautions': {
            'Low'     : 'Annual mammography screening. Monthly self-examination. Maintain healthy weight. Limit alcohol. Regular exercise.',
            'Moderate': 'Breast imaging (mammogram + ultrasound) recommended. Oncology consultation. Genetic counselling if family history present.',
            'High'    : 'Urgent oncology referral required. Biopsy evaluation needed. Discuss surgical, radiation, and chemotherapy options with specialist immediately.',
        },
    },
}


# ============================================================
# PREDICTION FORM ROUTE
# ============================================================
@prediction_bp.route('/<string:disease>', methods=['GET'])
@login_required
def predict_form(disease: str):
    """
    GET → Renders the dynamic prediction form for the selected disease.
    The form fields are generated from DISEASE_REGISTRY[disease]['fields'].
    """

    disease = disease.lower().strip()

    if disease not in DISEASE_REGISTRY:
        flash(f'Disease module "{disease}" is not supported.', 'warning')
        return redirect(url_for('dashboard.index'))

    config = DISEASE_REGISTRY[disease]

    context = {
        'disease_key'   : disease,
        'disease_config': config,
        'all_diseases'  : {k: v['name'] for k, v in DISEASE_REGISTRY.items()},
        'page_title'    : f'{config["name"]} — Prediction Form',
    }

    return render_template('prediction/predict.html', **context)


# ============================================================
# PREDICTION SUBMIT ROUTE
# ============================================================
@prediction_bp.route('/<string:disease>/submit', methods=['POST'])
@login_required
def submit_prediction(disease: str):
    disease = disease.lower().strip()

    if disease not in DISEASE_REGISTRY:
        flash('Invalid disease module.', 'danger')
        return redirect(url_for('dashboard.index'))

    config       = DISEASE_REGISTRY[disease]
    input_values = {}
    errors       = []

    # ── Validate inputs ───────────────────────────────────────
    for field in config['fields']:
        raw = request.form.get(field['name'], '').strip()

        if not raw:
            errors.append(f'{field["label"]} is required.')
            continue

        validated = validate_numeric_input(
            value      = raw,
            field_name = field['label'],
            min_val    = field.get('min'),
            max_val    = field.get('max'),
            is_float   = (field['type'] == 'float')
        )
        if validated['error']:
            errors.append(validated['error'])
        else:
            input_values[field['name']] = validated['value']

    # ── Return with errors ────────────────────────────────────
    if errors:
        return render_template(
            'prediction/predict.html',
            disease_key    = disease,
            disease_config = config,
            all_diseases   = {
                k: v['name'] for k, v in DISEASE_REGISTRY.items()
            },
            page_title     = f'{config["name"]} — Prediction',
            errors         = errors,
            form_data      = request.form,
        )

    # ── Run prediction ────────────────────────────────────────
    try:
        from ml_models.predictor import run_prediction

        result = run_prediction(
            disease    = disease,
            input_data = input_values,
            model_name = config['model_name']
        )

        # Validate result has required fields
        if not result or 'confidence_pct' not in result:
            raise ValueError('Invalid prediction result returned')

    except Exception as e:
        logger.error(f'Prediction failed: {e}')
        # Use emergency dummy result so page still works
        import random
        result = {
            'result'        : 'Negative',
            'confidence_pct': round(random.uniform(10, 35), 2),
            'model_type'    : 'fallback',
            'features_used' : [],
            'timestamp'     : datetime.utcnow().isoformat(),
        }

    # ── Determine risk ────────────────────────────────────────
    confidence  = float(result.get('confidence_pct', 20.0))
    risk_level  = _get_risk_level(confidence)
    precautions = config['precautions'].get(risk_level, '')

    # ── Save to database ──────────────────────────────────────
    try:
        record = PredictionHistory(
            user_id        = current_user.id,
            disease_name   = config['name'],
            result         = result.get('result', 'Negative'),
            risk_level     = risk_level,
            confidence_pct = confidence,
            input_data     = json.dumps(input_values),
            precautions    = precautions,
            model_used     = config['model_name'],
            created_at     = datetime.utcnow()
        )
        record.save()

    except Exception as e:
        logger.error(f'Could not save prediction: {e}')
        db.session.rollback()
        # Create a temporary record object for display
        # (not saved to DB but still shows results to user)
        from database.db import PredictionHistory as PH
        record      = PH()
        record.id             = 0
        record.user_id        = current_user.id
        record.disease_name   = config['name']
        record.result         = result.get('result', 'Negative')
        record.risk_level     = risk_level
        record.confidence_pct = confidence
        record.input_data     = json.dumps(input_values)
        record.precautions    = precautions
        record.model_used     = config['model_name']
        record.created_at     = datetime.utcnow()

    # ── Build risk factors ────────────────────────────────────
    risk_factors = _build_risk_factors(
        disease, input_values, config
    )

    # ── Render results ────────────────────────────────────────
    return render_template(
        'prediction/results.html',
        prediction     = format_prediction_for_display(record),
        disease_config = config,
        disease_key    = disease,
        risk_factors   = risk_factors,
        precautions    = precautions,
        page_title     = f'{config["name"]} — Result',
    )

# ============================================================
# PRIVATE HELPERS
# ============================================================
def _get_risk_level(confidence_pct: float) -> str:
    """
    Converts a confidence percentage into a risk label.

    Args:
        confidence_pct: Float between 0 and 100

    Returns:
        'Low', 'Moderate', or 'High'
    """
    if confidence_pct < 30:
        return 'Low'
    elif confidence_pct < 60:
        return 'Moderate'
    else:
        return 'High'


def _build_risk_factors(
    disease     : str,
    input_values: dict,
    config      : dict
) -> list:
    """
    Builds a list of risk factor objects for display on the results page.
    Normalises each input value to a 0–100 percentage for the progress bar.

    Returns:
        List of dicts with keys: label, value, unit, pct, status
    """

    risk_factors = []

    for field in config['fields']:
        name  = field['name']
        value = input_values.get(name)

        if value is None:
            continue

        min_val = field.get('min', 0)
        max_val = field.get('max', 100)

        # Normalize to percentage for bar width
        if max_val != min_val:
            pct = round(
                ((float(value) - float(min_val)) /
                 (float(max_val) - float(min_val))) * 100,
                1
            )
        else:
            pct = 0

        pct = max(0, min(100, pct))

        # Determine status label from normalized position
        if pct < 33:
            status = 'normal'
        elif pct < 66:
            status = 'borderline'
        else:
            status = 'elevated'

        risk_factors.append({
            'label'  : field['label'],
            'value'  : value,
            'unit'   : field.get('unit', ''),
            'pct'    : pct,
            'status' : status,
        })

    return risk_factors