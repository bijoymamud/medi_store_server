import sys
from src.database.connection import engine
from sqlalchemy import text, inspect

def clear_db():
    inspector = inspect(engine)
    all_tables = inspector.get_table_names()
    
    # Tables to keep
    keep_tables = {"users", "alembic_version"}
    
    # Tables to truncate
    truncate_tables = [t for t in all_tables if t not in keep_tables]
    
    if not truncate_tables:
        print("No tables found to truncate.")
        return
        
    print("WARNING: This will delete all data in the following tables:")
    for t in truncate_tables:
        print(f"  - {t}")
    print("The following tables will be KEPT:")
    for t in keep_tables:
        if t in all_tables:
            print(f"  - {t}")
            
    print("\nExecuting truncation...")
    
    # Construct the TRUNCATE query
    tables_csv = ", ".join(truncate_tables)
    query = text(f"TRUNCATE TABLE {tables_csv} RESTART IDENTITY CASCADE;")
    
    try:
        with engine.connect() as conn:
            conn.execute(query)
            conn.commit()
        print("\nDatabase cleared successfully (except users)!")
    except Exception as e:
        print(f"\nError executing truncation: {e}")

if __name__ == "__main__":
    clear_db()
