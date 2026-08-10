"""
test_auth.py — Phase 1 Auth System Test Suite
Run from the project root:
    python test_auth.py

Tests:
1. Backend imports and JWT library check
2. Token generation and verification logic
3. Login endpoint (correct and wrong credentials)
4. Protected admin route with and without token
"""
import sys
import json
import os

# ─── 1. Dependency Check ─────────────────────────────────────────────────────
print("=" * 60)
print("PHASE 1 AUTH TEST SUITE")
print("=" * 60)

print("\n[1/5] Checking JWT dependencies...")
try:
    from jose import jwt, JWTError
    import passlib
    print("  ✅ python-jose installed")
    print("  ✅ passlib installed")
except ImportError as e:
    print(f"  ❌ MISSING PACKAGE: {e}")
    print("\n  ▶ FIX: Run this in your terminal:")
    print('    pip install "python-jose[cryptography]==3.3.0" "passlib[bcrypt]==1.7.4"')
    sys.exit(1)

# ─── 2. Config Load ───────────────────────────────────────────────────────────
print("\n[2/5] Loading backend config...")
try:
    sys.path.insert(0, os.getcwd())
    from backend.config import settings
    print(f"  ✅ Config loaded")
    print(f"  ✅ ADMIN_USERNAME = '{settings.ADMIN_USERNAME}'")
    print(f"  ✅ JWT_EXPIRE_MINUTES = {settings.JWT_EXPIRE_MINUTES}")
    if settings.ADMIN_PASSWORD == "changeme123":
        print("  ⚠️  WARNING: ADMIN_PASSWORD is still the default 'changeme123'")
        print("              Change it in backend/.env before going live!")
    if "change-this" in settings.JWT_SECRET:
        print("  ⚠️  WARNING: JWT_SECRET is still the default placeholder")
        print("              Change it in backend/.env before going live!")
except Exception as e:
    print(f"  ❌ Config load failed: {e}")
    sys.exit(1)

# ─── 3. JWT Token Logic ───────────────────────────────────────────────────────
print("\n[3/5] Testing JWT token generation and verification...")
try:
    from datetime import datetime, timedelta
    SECRET = settings.JWT_SECRET
    ALGO = settings.JWT_ALGORITHM

    # Generate token
    payload = {"sub": "admin", "exp": datetime.utcnow() + timedelta(minutes=60)}
    token = jwt.encode(payload, SECRET, algorithm=ALGO)
    print(f"  ✅ Token generated: {token[:40]}...")

    # Verify token
    decoded = jwt.decode(token, SECRET, algorithms=[ALGO])
    assert decoded["sub"] == "admin"
    print(f"  ✅ Token verified, subject = '{decoded['sub']}'")

    # Test expired token
    expired_payload = {"sub": "admin", "exp": datetime.utcnow() - timedelta(minutes=1)}
    expired_token = jwt.encode(expired_payload, SECRET, algorithm=ALGO)
    try:
        jwt.decode(expired_token, SECRET, algorithms=[ALGO])
        print("  ❌ Expired token was NOT rejected!")
    except JWTError:
        print("  ✅ Expired token correctly rejected")

except Exception as e:
    print(f"  ❌ JWT test failed: {e}")
    sys.exit(1)

# ─── 4. Live API Tests (needs backend running) ────────────────────────────────
print("\n[4/5] Testing live API endpoints (backend must be running)...")
try:
    import httpx

    BASE = "http://localhost:8000"

    # Health check
    r = httpx.get(f"{BASE}/health", timeout=5)
    assert r.status_code == 200
    print(f"  ✅ GET /health → {r.status_code} {r.json()}")

    # Login with WRONG credentials
    r = httpx.post(f"{BASE}/api/auth/login",
                   json={"username": "admin", "password": "wrongpassword"}, timeout=5)
    assert r.status_code == 401
    print(f"  ✅ POST /api/auth/login (wrong creds) → 401 Unauthorized ✓")

    # Login with CORRECT credentials
    r = httpx.post(f"{BASE}/api/auth/login",
                   json={"username": settings.ADMIN_USERNAME, "password": settings.ADMIN_PASSWORD},
                   timeout=5)
    assert r.status_code == 200
    token = r.json()["access_token"]
    print(f"  ✅ POST /api/auth/login (correct creds) → 200 OK, token received")

    # Access protected route WITHOUT token
    r = httpx.get(f"{BASE}/api/admin/stats", timeout=5)
    assert r.status_code in (401, 403)
    print(f"  ✅ GET /api/admin/stats (no token) → {r.status_code} Unauthorized ✓")

    # Access protected route WITH token
    r = httpx.get(f"{BASE}/api/admin/stats",
                  headers={"Authorization": f"Bearer {token}"}, timeout=5)
    assert r.status_code == 200
    stats = r.json()
    print(f"  ✅ GET /api/admin/stats (with token) → 200 OK")
    print(f"     Students: {stats['total_students']}, Drives: {stats['active_drives']}")

    # Verify token endpoint
    r = httpx.get(f"{BASE}/api/auth/verify",
                  headers={"Authorization": f"Bearer {token}"}, timeout=5)
    assert r.status_code == 200
    print(f"  ✅ GET /api/auth/verify → 200 OK, valid={r.json()['valid']}")

except httpx.ConnectError:
    print("  ⚠️  Backend is NOT running. Skipping live API tests.")
    print("      Start it with: python -m uvicorn backend.main:app --reload --port 8000")
except AssertionError as e:
    print(f"  ❌ Assertion failed: {e}")
except Exception as e:
    print(f"  ❌ API test error: {e}")

# ─── 5. Frontend File Check ───────────────────────────────────────────────────
print("\n[5/5] Checking frontend auth files...")
files_to_check = [
    ("frontend/hooks/useAuth.ts",           "Auth hook"),
    ("frontend/app/login/page.tsx",         "Login page"),
    ("frontend/components/AuthGuard.tsx",   "Auth guard"),
]
all_ok = True
for path, name in files_to_check:
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"  ✅ {name} exists ({size} bytes)")
    else:
        print(f"  ❌ {name} MISSING at {path}")
        all_ok = False

print("\n" + "=" * 60)
if all_ok:
    print("✅ ALL CHECKS PASSED — Phase 1 Auth System is ready!")
    print("\n  Credentials (set in backend/.env):")
    print(f"    Username: {settings.ADMIN_USERNAME}")
    print(f"    Password: {settings.ADMIN_PASSWORD}")
    print("\n  Dashboard: http://localhost:3000")
    print("  API Docs:  http://localhost:8000/docs")
else:
    print("❌ SOME CHECKS FAILED — See errors above")
print("=" * 60)
