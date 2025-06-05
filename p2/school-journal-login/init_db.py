import sqlite3
import os
from pathlib import Path
import logging

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Database file path
DB_FILE = Path('school_journal.db')
SCHEMA_FILE = Path('schema.sql')

def init_db():
    """Initialize the database with required tables."""
    try:
        logger.info("Initializing database...")
        conn = sqlite3.connect(DB_FILE)
        
        # Read and execute schema file
        with open(SCHEMA_FILE, 'r') as f:
            sql = f.read()
            # Split SQL into individual statements
            statements = sql.split(';')
            cursor = conn.cursor()
            for statement in statements:
                if statement.strip():
                    logger.debug(f"Executing SQL statement: {statement.strip()}")
                    cursor.execute(statement)
            conn.commit()
            logger.info("Database initialized successfully!")
            
    except FileNotFoundError as e:
        logger.error(f"Schema file not found: {str(e)}")
        raise Exception("Schema file not found")
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {str(e)}")
        raise Exception("SQLite error occurred")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise Exception("Database initialization failed")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    init_db()
