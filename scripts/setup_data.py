#!/usr/bin/env python3
"""
Setup script to ensure critical data files exist for the NobelLM pipeline.

This script checks for required data files and creates them if missing,
either by copying from backups or generating minimal versions for testing.
"""

import os
import json
import shutil
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_and_restore_nobel_literature():
    """Check if nobel_literature.json exists, restore from backup if missing."""
    data_dir = Path("data")
    target_file = data_dir / "nobel_literature.json"
    
    if target_file.exists():
        logger.info("nobel_literature.json already exists")
        return True
    
    # Look for backup files
    backup_files = list(data_dir.glob("nobel_literature.json.*.bak"))
    if backup_files:
        # Use the most recent backup
        latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
        logger.info(f"Restoring nobel_literature.json from {latest_backup}")
        shutil.copy2(latest_backup, target_file)
        return True
    
    # Create minimal version for testing
    logger.warning("No backup found, creating minimal nobel_literature.json for testing")
    minimal_data = [
        {
            "year": 1993,
            "laureates": [{"full_name": "Toni Morrison", "country": "United States"}]
        },
        {
            "year": 2017,
            "laureates": [{"full_name": "Kazuo Ishiguro", "country": "United Kingdom"}]
        },
        {
            "year": 1989,
            "laureates": [{"full_name": "Camilo José Cela", "country": "Spain"}]
        },
        {
            "year": 2001,
            "laureates": [{"full_name": "V. S. Naipaul", "country": "United Kingdom"}]
        },
        {
            "year": 1995,
            "laureates": [{"full_name": "Seamus Heaney", "country": "Ireland"}]
        },
        {
            "year": 1990,
            "laureates": [{"full_name": "Octavio Paz", "country": "Mexico"}]
        }
    ]
    
    with open(target_file, 'w', encoding='utf-8') as f:
        json.dump(minimal_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Created minimal nobel_literature.json with {len(minimal_data)} entries")
    return True

def check_data_directory():
    """Ensure data directory exists."""
    data_dir = Path("data")
    if not data_dir.exists():
        logger.info("Creating data directory")
        data_dir.mkdir(parents=True, exist_ok=True)

def main():
    """Main setup function."""
    logger.info("Setting up critical data files...")
    
    check_data_directory()
    check_and_restore_nobel_literature()
    
    logger.info("Data setup complete!")

if __name__ == "__main__":
    main() 