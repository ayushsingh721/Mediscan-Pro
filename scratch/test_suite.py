# ============================================================
# scratch/test_suite.py — MediScan Pro Automated Verification Suite
# ============================================================

import os
import sys
import json
from datetime import datetime, date

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.db import db, User, UserProfile, PredictionHistory, DailyHealthTask, HealthReport
from ml_models.predictor import FEATURE_MAP, run_prediction
from utils.health_insights import generate_health_insights, get_personalized_tasks
from utils.pdf_generator import generate_pdf_report

print("=" * 60)
print("RUNNING MEDISCAN PRO VERIFICATION SUITE")
print("=" * 60)

app = create_app('testing')

with app.app_context():
    db.create_all()

    # ── Test 1: User & Profile Setup ─────────────────────────
    print("\n[TEST 1] Testing User and Health Profile...")
    test_email = 'clinical_test@mediscan.ai'
    u = User.query.filter_by(email=test_email).first()
    if not u:
        u = User(
            first_name='Clinical',
            last_name='Tester',
            email=test_email,
            age=42,
            gender='Male',
            is_active=True
        )
        u.set_password('TestPass123!')
        u.save()

    if not u.profile:
        prof = UserProfile(
            user_id=u.id,
            height_cm=180.0,
            weight_kg=78.0,
            blood_group='O+',
            smoking_status='Non-smoker',
            alcohol_status='Occasional',
            activity_level='Moderately Active'
        )
        prof.save()
    else:
        prof = u.profile
        prof.height_cm = 180.0
        prof.weight_kg = 78.0
        prof.save()

    assert u.current_bmi == 24.1, f"BMI mismatch: {u.current_bmi}"
    assert u.bmi_category['label'] == 'Normal Weight', f"BMI cat mismatch: {u.bmi_category}"
    print(f"[PASS] User created/verified: {u.full_name}, BMI: {u.current_bmi} ({u.bmi_category['label']})")

    # ── Test 2: Predictor Across All 8 Diseases ──────────────
    print("\n[TEST 2] Testing ML Prediction Across All 8 Diseases...")
    sample_inputs = {
        'diabetes': {'pregnancies': 2, 'glucose': 155, 'blood_pressure': 85, 'skin_thickness': 30, 'insulin': 120, 'bmi': 28.5, 'diabetes_pedigree': 0.45, 'age': 45},
        'heart': {'age': 58, 'sex': 1, 'cp': 2, 'trestbps': 145, 'chol': 260, 'fbs': 1, 'restecg': 1, 'thalach': 140, 'exang': 1, 'oldpeak': 2.2, 'slope': 1, 'ca': 1, 'thal': 2},
        'parkinsons': {'mdvp_fo': 150, 'mdvp_fhi': 180, 'mdvp_flo': 120, 'mdvp_jitter': 0.007, 'mdvp_shimmer': 0.045, 'nhr': 0.025, 'hnr': 22, 'rpde': 0.55, 'dfa': 0.7, 'spread1': -4.5, 'spread2': 0.25, 'd2': 2.3, 'ppe': 0.25},
        'kidney': {'age': 52, 'bp': 95, 'sg': 1.015, 'al': 2, 'su': 1, 'bgr': 160, 'bu': 48, 'sc': 1.6, 'sod': 136, 'pot': 4.5, 'hemo': 11.2, 'pcv': 34, 'wbcc': 8400, 'rbcc': 4.2},
        'liver': {'age': 48, 'gender': 1, 'total_bilirubin': 1.5, 'direct_bilirubin': 0.5, 'alkaline_phosphotase': 165, 'alamine_aminotransferase': 62, 'aspartate_aminotransferase': 45, 'total_proteins': 6.8, 'albumin': 3.2, 'albumin_globulin_ratio': 0.9},
        'lung_cancer': {'gender': 1, 'age': 55, 'smoking': 1, 'yellow_fingers': 1, 'anxiety': 0, 'peer_pressure': 0, 'chronic_disease': 1, 'fatigue': 1, 'allergy': 0, 'wheezing': 1, 'alcohol_consuming': 1, 'coughing': 1, 'shortness_of_breath': 1, 'swallowing_difficulty': 0, 'chest_pain': 1},
        'hypertension': {'age': 54, 'sex': 1, 'cp': 1, 'systolic_bp': 155, 'diastolic_bp': 95, 'cholesterol': 245, 'bmi': 31.0, 'smoking': 1, 'alcohol': 1, 'physical_activity': 0, 'family_history': 1},
        'breast_cancer': {'radius_mean': 17.5, 'texture_mean': 22.0, 'perimeter_mean': 115.0, 'area_mean': 850.0, 'smoothness_mean': 0.11, 'compactness_mean': 0.14, 'concavity_mean': 0.13, 'concave_points_mean': 0.08, 'symmetry_mean': 0.19, 'fractal_dimension_mean': 0.065}
    }

    predictions = {}
    for disease_key, inputs in sample_inputs.items():
        res = run_prediction(disease_key, inputs, f'{disease_key}_model')
        assert 'result' in res, f"Missing result for {disease_key}"
        assert 'confidence_pct' in res, f"Missing confidence for {disease_key}"
        assert 'risk_level' in res, f"Missing risk level for {disease_key}"
        predictions[disease_key] = res
        print(f"  [PASS] {disease_key:14}: Result={res['result']}, Risk={res['risk_level']}, Conf={res['confidence_pct']}%, Type={res['model_type']}")

    # ── Test 3: Educational Insights & Tasks ─────────────────
    print("\n[TEST 3] Testing Personalized Health Insights & Task Generation...")
    for disease_key in sample_inputs:
        pred_res = predictions[disease_key]
        ins = generate_health_insights(disease_key, pred_res['result'], pred_res['risk_level'], sample_inputs[disease_key], prof)
        assert len(ins['recommendations']) > 0, f"No recommendations for {disease_key}"
        assert len(ins['questions_for_doctor']) > 0, f"No doctor questions for {disease_key}"
        assert 'CLINICAL' in ins['disclaimer'].upper() or 'SCREENING' in ins['disclaimer'].upper()

        tasks = get_personalized_tasks(disease_key, pred_res['risk_level'])
        assert len(tasks) >= 4, f"Insufficient tasks for {disease_key}"

    print(f"[PASS] Verified health insights and personalized tasks for all 8 diseases.")

    # ── Test 4: Daily Health Tasks DB System ──────────────────
    print("\n[TEST 4] Testing Daily Health Tasks DB Persistence & Toggle...")
    DailyHealthTask.query.filter_by(user_id=u.id, target_date=date.today()).delete()
    DailyHealthTask.generate_default_tasks_for_user(u.id, disease_context='Diabetes Mellitus')
    today_tasks = DailyHealthTask.get_today_tasks(u.id)
    assert len(today_tasks) >= 5, f"Expected >= 5 tasks, got {len(today_tasks)}"

    task_to_toggle = today_tasks[0]
    init_state = task_to_toggle.is_completed
    DailyHealthTask.toggle_task(task_to_toggle.id, u.id)
    toggled = DailyHealthTask.query.get(task_to_toggle.id)
    assert toggled.is_completed != init_state, "Task toggle failed"
    print(f"[PASS] Daily tasks created ({len(today_tasks)} tasks) and toggle verified.")

    # ── Test 5: Professional PDF Generation ───────────────────
    print("\n[TEST 5] Testing ReportLab Clinical PDF Generator...")
    hist_rec = PredictionHistory.query.filter_by(user_id=u.id).first()
    if not hist_rec:
        hist_rec = PredictionHistory(
            user_id=u.id,
            disease_name='Diabetes Mellitus',
            result='Positive',
            risk_level='High',
            confidence_pct=68.5,
            input_data=json.dumps(sample_inputs['diabetes']),
            precautions='Consult endocrinologist. Begin daily glucose tracking.',
            model_used='diabetes_model',
            created_at=datetime.utcnow()
        )
        hist_rec.save()

    ins = generate_health_insights('diabetes', hist_rec.result, hist_rec.risk_level, sample_inputs['diabetes'], prof)
    pdf_buf = generate_pdf_report(u, hist_rec, prof, ins)
    pdf_data = pdf_buf.getvalue()

    assert len(pdf_data) > 3000, f"PDF too small ({len(pdf_data)} bytes)"
    assert pdf_data.startswith(b'%PDF'), "Not a valid PDF header"
    print(f"[PASS] Generated valid ReportLab clinical PDF ({len(pdf_data)} bytes).")

    # ── Test 6: Security & User Isolation ─────────────────────
    print("\n[TEST 6] Testing User Data Isolation...")
    u2 = User.query.filter_by(email='other_user@mediscan.ai').first()
    if not u2:
        u2 = User(first_name='Other', last_name='Patient', email='other_user@mediscan.ai', is_active=True)
        u2.set_password('Pass12345!')
        u2.save()

    # Verify u cannot access u2's predictions
    u2_pred = PredictionHistory.query.filter_by(user_id=u2.id).first()
    if not u2_pred:
        u2_pred = PredictionHistory(
            user_id=u2.id,
            disease_name='Heart Disease',
            result='Negative',
            risk_level='Low',
            confidence_pct=15.0,
            created_at=datetime.utcnow()
        )
        u2_pred.save()

    assert PredictionHistory.get_by_id(u2_pred.id, u.id) is None, "Isolation breach: user accessed another user's prediction!"
    print("[PASS] Strict user data isolation verified: User A cannot query User B records.")

print("\n" + "=" * 60)
print("ALL VERIFICATION SUITE TESTS PASSED!")
print("=" * 60)
