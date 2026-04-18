import pandas as pd
from sqlalchemy import create_engine, text
import os

# ──────────────────────────────────────────────
# ⚠️  UPDATE THESE WITH YOUR POSTGRES CREDENTIALS
# ──────────────────────────────────────────────
DB_USER = "postgres"
DB_PASS = "om*7489"       # ← change this
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "bhopal_smart_city"
DATA_DIR = "Data/cleaned"           # ← path to your CSVs (relative to this script)
# ──────────────────────────────────────────────

engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

def load_table(csv_file, table_name, date_cols=None, drop_cols=None):
    """Load a CSV into a PostgreSQL table cleanly."""
    path = os.path.join(DATA_DIR, csv_file)
    df = pd.read_csv(path)

    # Drop auto-generated ID columns (PostgreSQL SERIAL handles these)
    if drop_cols:
        df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    # Parse date columns
    if date_cols:
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

    # Load into PostgreSQL
    df.to_sql(table_name, engine, if_exists='append', index=False)
    print(f"  ✅  {table_name:25s} → {len(df):>7,} rows loaded")
    return len(df)

print("\n🚀 Loading all tables into bhopal_smart_city database...\n")

try:
    total = 0

    # 1. Wards — load first (other tables reference it)
    total += load_table(
        csv_file  = "wards_cleaned.csv",
        table_name= "wards",
        drop_cols = ["ward_id"]
    )

    # 2. Smart City Projects
    total += load_table(
        csv_file  = "smart_city_projects_cleaned.csv",
        table_name= "smart_city_projects",
        date_cols = ["start_date", "expected_end", "actual_end"],
        drop_cols = ["project_id"]
    )

    # 3. Healthcare
    total += load_table(
        csv_file  = "healthcare_cleaned.csv",
        table_name= "healthcare",
        drop_cols = ["facility_id"]
    )

    # 4. Air Quality — the one that was failing
    total += load_table(
        csv_file  = "air_quality_cleaned.csv",
        table_name= "air_quality",
        date_cols = ["reading_date"],
        drop_cols = ["aqi_id"]
    )

    # 5. Lake Quality
    total += load_table(
        csv_file  = "lake_quality_cleaned.csv",
        table_name= "lake_quality",
        date_cols = ["sample_date"],
        drop_cols = ["lake_id"]
    )

    # 6. Complaints — largest table, takes ~30 seconds
    print("  ⏳  complaints — large file, please wait (~30 sec)...")
    total += load_table(
        csv_file  = "complaints_cleaned.csv",
        table_name= "complaints",
        date_cols = ["complaint_date"],
        drop_cols = ["complaint_id"]
    )

    print(f"\n🎉 Done! Total rows loaded: {total:,}")

    # ── Verification Query ──────────────────────
    print("\n📊 Verifying row counts in database:\n")
    verify_sql = """
        SELECT 'wards'               AS table_name, COUNT(*) AS rows FROM wards
        UNION ALL
        SELECT 'smart_city_projects',               COUNT(*)          FROM smart_city_projects
        UNION ALL
        SELECT 'healthcare',                         COUNT(*)          FROM healthcare
        UNION ALL
        SELECT 'air_quality',                        COUNT(*)          FROM air_quality
        UNION ALL
        SELECT 'lake_quality',                       COUNT(*)          FROM lake_quality
        UNION ALL
        SELECT 'complaints',                         COUNT(*)          FROM complaints
        ORDER BY table_name;
    """
    with engine.connect() as conn:
        result = conn.execute(text(verify_sql))
        print(f"  {'Table':<25} {'Rows':>10}")
        print(f"  {'-'*25} {'-'*10}")
        for row in result:
            print(f"  {row[0]:<25} {row[1]:>10,}")

    print("\n✅ All tables loaded and verified. Day 1 complete!\n")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\n💡 Check:")
    print("   1. DB_PASS is correct")
    print("   2. PostgreSQL is running")
    print("   3. Database 'bhopal_smart_city' exists")
    print("   4. DATA_DIR path points to your CSV folder")