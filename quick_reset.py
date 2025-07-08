#!/usr/bin/env python3
"""
Quick script to drop and recreate all tables
No confirmation prompts - use with caution!
"""

from database import engine
import models
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def quick_reset():
    """Drop and recreate all tables quickly"""
    try:
        logger.info("🗑️  Dropping all tables...")
        models.Base.metadata.drop_all(bind=engine)
        
        logger.info("🔨 Creating all tables...")
        models.Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Tables reset successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    quick_reset()