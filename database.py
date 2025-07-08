from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database configuration
DB_TYPE = os.getenv("DB_TYPE", "local")  # "local" or "supabase"

if DB_TYPE == "supabase":
    # Supabase configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")
    
    if not SUPABASE_DB_URL:
        raise ValueError("SUPABASE_DB_URL environment variable is required for Supabase")
    
    SQLALCHEMY_DATABASE_URL = SUPABASE_DB_URL
    logger.info(f"🔗 Configuring Supabase database connection")
    logger.info(f"📊 Database: {SUPABASE_DB_URL.split('@')[1] if '@' in SUPABASE_DB_URL else 'Supabase'}")
else:
    # Local PostgreSQL configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "expense_tracker")
    DB_USER = os.getenv("DB_USER", "expense_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "asdfasdf")
    
    SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    logger.info(f"🔗 Configuring local PostgreSQL database connection")
    logger.info(f"📊 Database: {DB_HOST}:{DB_PORT}/{DB_NAME}")

engine = create_engine(SQLALCHEMY_DATABASE_URL)

def test_database_connection():
    """Test database connection and log the result"""
    try:
        with engine.connect() as connection:
            logger.info(f"✅ Successfully connected to {DB_TYPE} database!")
            logger.info(f"🎯 Database URL: {str(engine.url).replace(str(engine.url).split('@')[0].split('://')[-1], '***')}")
            return True
    except Exception as e:
        logger.error(f"❌ Failed to connect to {DB_TYPE} database: {str(e)}")
        return False

# Test connection on startup
test_database_connection()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
