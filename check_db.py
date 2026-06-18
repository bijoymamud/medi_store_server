from src.database.connection import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        # Get column names and types
        cols = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'orders';")).fetchall()
        print("Columns:")
        for col in cols:
            print(f"  {col[0]}: {col[1]}")
            
        # Get constraints
        constraints = conn.execute(text("SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'orders'::regclass;")).fetchall()
        print("\nConstraints:")
        for con in constraints:
            print(f"  {con[0]}: {con[1]}")
    except Exception as e:
        print(f"Error checking DB schema: {e}")
