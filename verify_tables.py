#!/usr/bin/env python3
"""
Simple script to verify all tables exist and show their structure
"""

from sqlalchemy import inspect
from database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_tables():
    """Verify all expected tables exist"""
    
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        expected_tables = ['users', 'categories', 'expenses', 'login_attempts']
        
        logger.info("📊 Database Table Verification:")
        logger.info("=" * 50)
        
        for table in expected_tables:
            if table in existing_tables:
                logger.info(f"✅ {table} - EXISTS")
                
                # Show columns
                columns = inspector.get_columns(table)
                logger.info(f"   Columns ({len(columns)}):")
                for column in columns:
                    nullable = "NULL" if column['nullable'] else "NOT NULL"
                    logger.info(f"     - {column['name']}: {column['type']} {nullable}")
                
                logger.info("")
            else:
                logger.error(f"❌ {table} - MISSING")
        
        logger.info(f"📋 Total tables in database: {len(existing_tables)}")
        logger.info(f"📋 All tables: {existing_tables}")
        
        if set(expected_tables).issubset(set(existing_tables)):
            logger.info("🎉 All expected tables exist!")
            return True
        else:
            logger.error("❌ Some expected tables are missing!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verifying tables: {e}")
        return False

if __name__ == "__main__":
    verify_tables()