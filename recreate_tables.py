#!/usr/bin/env python3
"""
Script to recreate all tables using SQLAlchemy's built-in methods
This is safer as it handles foreign key constraints automatically
"""

from sqlalchemy import inspect
from database import engine
import models
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_all_tables():
    """Drop and recreate all tables using SQLAlchemy"""
    
    try:
        # Get inspector to check existing tables before dropping
        inspector = inspect(engine)
        existing_tables_before = inspector.get_table_names()
        
        if existing_tables_before:
            logger.info(f"📋 Found {len(existing_tables_before)} existing tables: {existing_tables_before}")
        else:
            logger.info("📋 No existing tables found")
        
        # Drop all tables using SQLAlchemy (handles foreign keys automatically)
        logger.info("🗑️  Dropping all tables using SQLAlchemy...")
        models.Base.metadata.drop_all(bind=engine)
        logger.info("✅ All tables dropped successfully")
        
        # Verify tables were dropped
        inspector = inspect(engine)
        remaining_tables = inspector.get_table_names()
        
        if remaining_tables:
            logger.warning(f"⚠️  Some tables still exist: {remaining_tables}")
        else:
            logger.info("✅ All tables confirmed dropped")
        
        # Create all tables using SQLAlchemy
        logger.info("🔨 Creating all tables using SQLAlchemy...")
        models.Base.metadata.create_all(bind=engine)
        logger.info("✅ All tables created successfully")
        
        # Verify tables were created
        inspector = inspect(engine)
        new_tables = inspector.get_table_names()
        
        expected_tables = ['users', 'categories', 'expenses', 'login_attempts']
        
        logger.info("📊 Verifying created tables:")
        for table in expected_tables:
            if table in new_tables:
                logger.info(f"  ✅ {table} - created")
            else:
                logger.error(f"  ❌ {table} - missing")
        
        logger.info(f"📋 All tables in database: {new_tables}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error recreating tables: {e}")
        raise

def show_table_details():
    """Show detailed information about all tables"""
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        for table in tables:
            logger.info(f"\n🔍 Table: {table}")
            
            # Show columns
            columns = inspector.get_columns(table)
            logger.info("  Columns:")
            for column in columns:
                nullable = "NULL" if column['nullable'] else "NOT NULL"
                default = f" DEFAULT {column['default']}" if column.get('default') else ""
                primary_key = " PRIMARY KEY" if column.get('primary_key') else ""
                logger.info(f"    - {column['name']}: {column['type']} {nullable}{default}{primary_key}")
            
            # Show indexes
            indexes = inspector.get_indexes(table)
            if indexes:
                logger.info("  Indexes:")
                for index in indexes:
                    unique = " UNIQUE" if index['unique'] else ""
                    logger.info(f"    - {index['name']}: {index['column_names']}{unique}")
            
            # Show foreign keys
            foreign_keys = inspector.get_foreign_keys(table)
            if foreign_keys:
                logger.info("  Foreign Keys:")
                for fk in foreign_keys:
                    logger.info(f"    - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
                    
    except Exception as e:
        logger.error(f"❌ Error showing table details: {e}")

def main():
    """Main function"""
    
    print("⚠️  WARNING: This will DELETE ALL DATA in the database!")
    print("This will drop and recreate all tables using SQLAlchemy.")
    print("This action cannot be undone.")
    
    # Ask for confirmation
    confirm = input("\nAre you sure you want to proceed? (yes/no): ").lower().strip()
    
    if confirm != 'yes':
        logger.info("❌ Operation cancelled by user")
        return
    
    logger.info("🔄 Starting table recreation...")
    
    try:
        # Recreate all tables
        recreate_all_tables()
        
        # Show table details
        logger.info("\n📝 Table Details:")
        show_table_details()
        
        logger.info("\n🎉 Table recreation completed successfully!")
        logger.info("✅ All tables have been recreated with proper structure")
        
    except Exception as e:
        logger.error(f"❌ Table recreation failed: {e}")
        raise

if __name__ == "__main__":
    main()