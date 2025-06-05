import os
import sys
import logging
from app import app

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Check if schema.sql exists
SCHEMA_FILE = 'schema.sql'
if not os.path.exists(SCHEMA_FILE):
    logger.error(f"Schema file {SCHEMA_FILE} not found. Please create it first.")
    sys.exit(1)

# Check if required directories exist
TEMPLATES_DIR = 'templates'
STATIC_DIR = 'static'
if not os.path.exists(TEMPLATES_DIR):
    logger.error(f"Templates directory {TEMPLATES_DIR} not found.")
    sys.exit(1)
if not os.path.exists(STATIC_DIR):
    logger.error(f"Static directory {STATIC_DIR} not found.")
    sys.exit(1)

# Start Flask app
if __name__ == '__main__':
    try:
        logger.info("Starting Flask application...")
        # Initialize app first
        from app import initialize_app
        initialize_app()
        
        # Then run the app
        app.run(debug=True, port=5001)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        sys.exit(1)
