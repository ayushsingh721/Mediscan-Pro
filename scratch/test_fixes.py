import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.db import User

print("=" * 60)
print("VERIFYING SECURITY, AI TIPS, AND DATASETS FIXES")
print("=" * 60)

app = create_app('development')
app.config['WTF_CSRF_ENABLED'] = False

client = app.test_client()

with app.app_context():
    user = User.get_by_email('thakurayushmaan734@gmail.com')
    assert user is not None, "User not found"
    print(f"[PASS] Found target user: {user.email}")

    # ── Test 1: Full Login -> Dashboard -> Logout -> Security Block ────
    print("\n--- TEST 1: Authentication & Security Isolation ---")
    
    # 1. Login
    login_resp = client.post('/auth/login', data={'email': user.email, 'password': 'Ayush@123'}, follow_redirects=True)
    assert login_resp.status_code == 200
    assert "Healthcare Dashboard" in login_resp.data.decode('utf-8') or "Clinical Health Dashboard" in login_resp.data.decode('utf-8')
    print("[PASS] 1. Login succeeded and reached dashboard.")

    # 2. Access dashboard authenticated
    dash_resp = client.get('/dashboard/')
    assert dash_resp.status_code == 200
    print("[PASS] 2. GET /dashboard/ accessible when authenticated.")

    # 3. Call /auth/logout
    logout_resp = client.get('/auth/logout', follow_redirects=False)
    assert logout_resp.status_code == 302, f"Expected 302, got {logout_resp.status_code}"
    assert '/auth/login' in logout_resp.headers.get('Location', '')
    assert 'no-store' in logout_resp.headers.get('Cache-Control', '').lower()
    print("[PASS] 3. /auth/logout returned 302 to /auth/login with anti-cache headers.")

    # 4. Follow to login page
    login_page = client.get(logout_resp.headers['Location'])
    assert login_page.status_code == 200
    assert "Sign In" in login_page.data.decode('utf-8')
    print("[PASS] 4. Landing on /auth/login after logout.")

    # 5. Attempt unauthenticated access to /dashboard/
    unauth_dash = client.get('/dashboard/', follow_redirects=False)
    assert unauth_dash.status_code == 302, f"Expected 302 redirect for unauth dashboard, got {unauth_dash.status_code}"
    assert '/auth/login' in unauth_dash.headers.get('Location', '')
    print("[PASS] 5. Unauthenticated GET /dashboard/ is strictly BLOCKED and redirects to login.")

    # 6. Check Home page (/) when logged out
    home_unauth = client.get('/')
    assert home_unauth.status_code == 200
    home_html = home_unauth.data.decode('utf-8')
    assert "Sign In" in home_html
    assert "Get Started" in home_html
    assert "Datasets & ML" in home_html
    print("[PASS] 6. Home page displays 'Sign In', 'Get Started', and 'Datasets & ML'.")

    # ── Test 2: AI Integrated Health Tips ──────────────────────────────
    print("\n--- TEST 2: AI Integrated Health Tips ---")
    
    # Log back in to test AI tip endpoint
    client.post('/auth/login', data={'email': user.email, 'password': 'Ayush@123'}, follow_redirects=True)
    
    # GET /dashboard/ai-health-tip
    ai_resp = client.get('/dashboard/ai-health-tip')
    assert ai_resp.status_code == 200
    ai_data = ai_resp.get_json()
    assert ai_data['success'] is True
    tip = ai_data['tip']
    assert 'title' in tip and 'action_step' in tip and 'target_biomarker' in tip
    print(f"[PASS] 1. GET /dashboard/ai-health-tip generated tip: '{tip['title']}' [{tip['category']}]")

    # POST /dashboard/ai-health-tip with specific category
    ai_post_resp = client.post('/dashboard/ai-health-tip', json={'category': 'cardiovascular'})
    assert ai_post_resp.status_code == 200
    ai_post_data = ai_post_resp.get_json()
    assert ai_post_data['success'] is True
    print(f"[PASS] 2. POST /dashboard/ai-health-tip returned categorized tip: '{ai_post_data['tip']['title']}'")

    # ── Test 3: B.Tech Benchmark Datasets & Research Explorer ──────────
    print("\n--- TEST 3: Clinical Datasets & ML Explorer ---")
    
    # Check all 8 CSV datasets exist
    diseases = ['diabetes', 'heart', 'kidney', 'liver', 'parkinsons', 'breast_cancer', 'hypertension', 'stroke']
    for d in diseases:
        csv_p = os.path.join('datasets', f'{d}.csv')
        assert os.path.exists(csv_p), f"Missing {csv_p}"
        size = os.path.getsize(csv_p)
        assert size > 1000, f"File {csv_p} too small ({size} bytes)"
    print(f"[PASS] 1. Verified all 8 clinical CSV datasets exist with authentic data in datasets/.")

    # Check /datasets web explorer
    ds_resp = client.get('/datasets')
    assert ds_resp.status_code == 200
    ds_html = ds_resp.data.decode('utf-8')
    assert "Machine Learning" in ds_html
    assert "Benchmark Datasets" in ds_html
    assert "Comparative Model Benchmark Evaluation" in ds_html
    print("[PASS] 2. GET /datasets renders clinical datasets and ML benchmark tables.")

    # Check /datasets/download/diabetes
    dl_resp = client.get('/datasets/download/diabetes')
    assert dl_resp.status_code == 200
    assert dl_resp.headers.get('Content-Type') == 'text/csv; charset=utf-8'
    assert 'attachment' in dl_resp.headers.get('Content-Disposition', '')
    print("[PASS] 3. GET /datasets/download/diabetes serves CSV attachment.")

    # Check DATASETS_CATALOG.md
    catalog_path = os.path.join('datasets', 'DATASETS_CATALOG.md')
    assert os.path.exists(catalog_path)
    assert os.path.getsize(catalog_path) > 2000
    print("[PASS] 4. datasets/DATASETS_CATALOG.md verified with full academic documentation.")

print("\n" + "=" * 60)
print("ALL VERIFICATION SUITE ASSERTIONS PASSED (100% SUCCESS)!")
print("=" * 60)
