# ============================================================
# scratch/test_client_flow.py — End-to-End Flask Client Simulation
# ============================================================

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.db import db, User, UserProfile, PredictionHistory, DailyHealthTask

app = create_app('development')
app.config['WTF_CSRF_ENABLED'] = False  # disable CSRF for test client ease

client = app.test_client()

print("=" * 60)
print("RUNNING E2E FLASK CLIENT SIMULATION")
print("=" * 60)

with app.app_context():
    user = User.get_by_email('thakurayushmaan734@gmail.com')
    print(f"Target User: {user.full_name} ({user.email})")

    # 1. Login session simulation
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['user_id'] = user.id
        sess['user_name'] = user.full_name

    # 2. GET Dashboard
    resp = client.get('/dashboard/')
    assert resp.status_code == 200, f"Dashboard failed with {resp.status_code}"
    html = resp.data.decode('utf-8')
    assert "Healthcare Dashboard" in html or "Clinical Health Dashboard" in html
    assert "Today's Health Tasks" in html
    print("[PASS] 1. GET /dashboard/ returned 200 and rendered modern dashboard.")

    # 3. Toggle Daily Task
    tasks = DailyHealthTask.get_today_tasks(user.id)
    assert len(tasks) > 0
    test_task = tasks[0]
    toggle_resp = client.post(f'/dashboard/tasks/{test_task.id}/toggle')
    assert toggle_resp.status_code == 200
    toggle_data = toggle_resp.get_json()
    assert toggle_data['success'] is True
    print(f"[PASS] 2. POST /dashboard/tasks/{test_task.id}/toggle returned 200: is_completed={toggle_data['is_completed']}")

    # 4. POST Update Health Profile
    profile_data = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'age': 24,
        'gender': 'Male',
        'phone': '+91 9876543210',
        'height_cm': 178,
        'weight_kg': 72,
        'blood_group': 'B+',
        'smoking_status': 'Non-smoker',
        'alcohol_status': 'None',
        'activity_level': 'Moderately Active',
        'existing_conditions': 'None',
        'allergies': 'None',
        'emergency_contact_name': 'Parent',
        'emergency_contact_phone': '+91 9876500000'
    }
    prof_resp = client.post('/dashboard/profile/update', data=profile_data, follow_redirects=True)
    assert prof_resp.status_code == 200
    user = User.get_by_id(user.id)
    assert user.current_bmi == 22.7
    print(f"[PASS] 3. POST /dashboard/profile/update succeeded! BMI calculated: {user.current_bmi} ({user.bmi_category['label']})")

    # 5. GET Prediction Form
    form_resp = client.get('/predict/diabetes')
    assert form_resp.status_code == 200
    assert "Diabetes Mellitus" in form_resp.data.decode('utf-8')
    print("[PASS] 4. GET /predict/diabetes returned 200 with dynamic clinical input fields.")

    # 6. POST Prediction Submit
    diabetes_inputs = {
        'pregnancies': '1',
        'glucose': '138',
        'blood_pressure': '84',
        'skin_thickness': '28',
        'insulin': '135',
        'bmi': '27.4',
        'diabetes_pedigree': '0.52',
        'age': '48'
    }
    sub_resp = client.post('/predict/diabetes/submit', data=diabetes_inputs)
    assert sub_resp.status_code == 200
    sub_html = sub_resp.data.decode('utf-8')
    assert "Clinical Screening Results" in sub_html
    assert "Download PDF Clinical Report" in sub_html
    assert "Personalized Health Insights" in sub_html
    assert "CLINICAL SCREENING DISCLAIMER" in sub_html
    print("[PASS] 5. POST /predict/diabetes/submit generated modern prediction results with insights, tasks, and disclaimer.")

    # 7. GET PDF Report Download
    latest_pred = user.latest_prediction
    assert latest_pred is not None
    pdf_resp = client.get(f'/dashboard/report/{latest_pred.id}/download')
    assert pdf_resp.status_code == 200
    assert pdf_resp.content_type == 'application/pdf'
    assert 'attachment;' in pdf_resp.headers.get('Content-Disposition', '')
    assert pdf_resp.data.startswith(b'%PDF')
    print(f"[PASS] 6. GET /dashboard/report/{latest_pred.id}/download returned 200 application/pdf ({len(pdf_resp.data)} bytes).")

    # 8. GET PDF Inline View
    view_resp = client.get(f'/dashboard/report/{latest_pred.id}/view')
    assert view_resp.status_code == 200
    assert view_resp.content_type == 'application/pdf'
    assert 'inline;' in view_resp.headers.get('Content-Disposition', '')
    print(f"[PASS] 7. GET /dashboard/report/{latest_pred.id}/view returned 200 with inline PDF preview.")

    # 9. GET Health History
    hist_resp = client.get('/dashboard/history')
    assert hist_resp.status_code == 200
    hist_html = hist_resp.data.decode('utf-8')
    assert "Health Timeline &amp; Reports" in hist_html or "Health Timeline" in hist_html
    print("[PASS] 8. GET /dashboard/history returned 200 with timeline records.")

print("\n" + "=" * 60)
print("E2E FLASK CLIENT SIMULATION COMPLETE: ALL ASSERTIONS PASSED!")
print("=" * 60)
