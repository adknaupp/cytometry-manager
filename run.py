import os
import sys
import uvicorn

from app.database import init_db, load_csv, DB_FILE, CSV_FILE

if __name__ == "__main__":
    if not os.path.exists(DB_FILE):
        init_db()
        load_csv()
        print(f'Database initialized and CSV "{CSV_FILE}" loaded.')
    else:
        print(f"Database file '{DB_FILE}' already exists. Skipping initialization and CSV loading.")
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload="--reload" in sys.argv
    )
