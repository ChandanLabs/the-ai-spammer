import os
from backend.config import settings
from backend.models.database import engine
from sqlalchemy import text

print("====================================")
print(f"Testing DB URL: {settings.DATABASE_URL}")
print("====================================")

try:
    # Test 1: Can we connect to the DB?
    print("Test 1: Connecting to Supabase...")
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version()")).fetchone()
        print(f"✅ Success! Connected to: {version[0]}")
    
    # Test 2: Can we create tables? (This is where main.py crashed)
    print("\nTest 2: Creating tables (Base.metadata.create_all)...")
    from backend.models import Base
    from backend.models.schemas import HiringDrive, Student, NudgeLog
    Base.metadata.create_all(bind=engine)
    print("✅ Success! Tables verified/created.")

    print("\n✅ ALL TESTS PASSED. The app should NOT be crashing because of the DB.")
except Exception as e:
    import traceback
    print("\n❌ CRASH DETECTED!")
    print("Here is the exact error:")
    traceback.print_exc()
