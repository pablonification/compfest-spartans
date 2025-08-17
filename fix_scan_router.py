#!/usr/bin/env python3
"""
Script to fix the scan router file
"""

def fix_scan_router():
    """Fix the scan router file by replacing the broken router definition"""
    
    file_path = 'backend/src/backend/routers/scan.py'
    
    try:
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Replace the broken router definition
        old_def = 'router = APIRouter(prefix=/scan, tags=[scan])'
        new_def = 'router = APIRouter(prefix="/scan", tags=["scan"])'
        
        if old_def in content:
            content = content.replace(old_def, new_def)
            print(f"Found and replaced: {old_def}")
        else:
            print("Broken router definition not found")
            return False
        
        # Write the fixed content back
        with open(file_path, 'w') as f:
            f.write(content)
        
        print("Scan router file fixed successfully!")
        return True
        
    except Exception as e:
        print(f"Error fixing scan router: {e}")
        return False

if __name__ == "__main__":
    fix_scan_router()

