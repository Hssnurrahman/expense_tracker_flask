#!/usr/bin/env python3
"""
Script to drop all tables and recreate them
WARNING: This will delete ALL data in the database
"""

from sqlalchemy import create_engine, inspect, text
from database import engine
import models
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def drop_all_tables():
    """Drop all tables in the database"""
    
    try:
        # Get inspector to check existing tables
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if not existing_tables:
            logger.info("No tables found to drop")
            return
        
        logger.info(f"📋 Found {len(existing_tables)} tables to drop: {existing_tables}")
        
        with engine.connect() as connection:
            # Drop tables in reverse order to handle foreign key constraints
            for table in reversed(existing_tables):
                logger.info(f"🗑️  Dropping table: {table}")
                connection.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
            
            connection.commit()
            logger.info("✅ All tables dropped successfully")
            
    except Exception as e:
        logger.error(f"❌ Error dropping tables: {e}")
        raise

def create_all_tables():
    """Create all tables using SQLAlchemy"""
    
    try:
        # Create all tables defined in models.py
        models.Base.metadata.create_all(bind=engine)
        logger.info("✅ All tables created successfully")
        
        # Verify tables were created
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        expected_tables = ['users', 'categories', 'expenses', 'login_attempts']
        
        logger.info("📊 Verifying created tables:")
        for table in expected_tables:
            if table in existing_tables:
                logger.info(f"  ✅ {table} - created")
            else:
                logger.error(f"  ❌ {table} - missing")
        
        logger.info(f"📋 All tables in database: {existing_tables}")
        
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        raise

def show_table_structures():
    """Show the structure of all tables"""
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        for table in tables:
            logger.info(f"\n🔍 Table: {table}")
            columns = inspector.get_columns(table)
            
            for column in columns:
                nullable = "NULL" if column['nullable'] else "NOT NULL"
                default = f" DEFAULT {column['default']}" if column.get('default') else ""
                logger.info(f"  - {column['name']}: {column['type']} {nullable}{default}")
                
    except Exception as e:
        logger.error(f"❌ Error showing table structures: {e}")

def main():
    """Main function to reset database"""
    
    print("⚠️  WARNING: This will DELETE ALL DATA in the database!")
    print("This action cannot be undone.")
    
    # Ask for confirmation
    confirm = input("\nAre you sure you want to proceed? (yes/no): ").lower().strip()
    
    if confirm != 'yes':
        logger.info("❌ Operation cancelled by user")
        return
    
    # Double confirmation
    confirm2 = input("\nType 'DELETE ALL DATA' to confirm: ").strip()
    
    if confirm2 != 'DELETE ALL DATA':
        logger.info("❌ Operation cancelled - incorrect confirmation")
        return
    
    logger.info("🔄 Starting database reset...")
    
    try:
        # Step 1: Drop all tables
        logger.info("\n📝 Step 1: Dropping all tables...")
        drop_all_tables()
        
        # Step 2: Create all tables
        logger.info("\n📝 Step 2: Creating all tables...")
        create_all_tables()
        
        # Step 3: Show table structures
        logger.info("\n📝 Step 3: Showing table structures...")
        show_table_structures()
        
        logger.info("\n🎉 Database reset completed successfully!")
        logger.info("✅ All tables have been recreated")
        
    except Exception as e:
        logger.error(f"❌ Database reset failed: {e}")
        raise

if __name__ == "__main__":
    main()