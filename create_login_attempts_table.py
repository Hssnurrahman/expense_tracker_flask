#!/usr/bin/env python3
"""
Script to create the login_attempts table
Run this if you need to manually create the table
"""

from sqlalchemy import create_engine, text
from database import SQLALCHEMY_DATABASE_URL, engine
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_login_attempts_table():
    """Create the login_attempts table manually"""
    
    # SQL to create the login_attempts table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS login_attempts (
        id SERIAL PRIMARY KEY,
        username VARCHAR NOT NULL,
        ip_address VARCHAR,
        success INTEGER DEFAULT 0,
        timestamp TIMESTAMP NOT NULL
    );
    
    CREATE INDEX IF NOT EXISTS idx_login_attempts_username ON login_attempts(username);
    CREATE INDEX IF NOT EXISTS idx_login_attempts_timestamp ON login_attempts(timestamp);
    """
    
    try:
        with engine.connect() as connection:
            # Execute the CREATE TABLE statement
            connection.execute(text(create_table_sql))
            connection.commit()
            logger.info("✅ login_attempts table created successfully")
            
            # Verify the table was created
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'login_attempts'
            """))
            
            if result.fetchone():
                logger.info("✅ login_attempts table verified in database")
            else:
                logger.error("❌ login_attempts table not found after creation")
                
    except Exception as e:
        logger.error(f"❌ Error creating login_attempts table: {e}")
        raise

def check_table_exists():
    """Check if the login_attempts table exists"""
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'login_attempts'
            """))
            
            if result.fetchone():
                logger.info("✅ login_attempts table already exists")
                return True
            else:
                logger.info("⚠️  login_attempts table does not exist")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error checking table existence: {e}")
        return False

def main():
    """Main function to create the table"""
    logger.info("🔧 Creating login_attempts table...")
    
    # Check if table already exists
    if check_table_exists():
        logger.info("Table already exists, no action needed")
        return
    
    # Create the table
    create_login_attempts_table()
    
    logger.info("🎉 login_attempts table setup complete!")

if __name__ == "__main__":
    main()