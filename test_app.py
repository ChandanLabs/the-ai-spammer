import sys
print("Test: Importing FastAPI app...")
try:
    from backend.main import app
    print("✅ Success! The app imported correctly.")
except Exception as e:
    import traceback
    print("❌ CRASH DETECTED on import!")
    traceback.print_exc()
    sys.exit(1)
