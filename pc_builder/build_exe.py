#!/usr/bin/env python3
"""
Build script for PC Builder Application
This script provides instructions and alternative build methods.
"""

import os
import sys
import subprocess

def check_dependencies():
    """Check if required dependencies are available"""
    print("Checking dependencies...")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check if tkinter is available
    try:
        import tkinter
        print("✓ tkinter is available")
    except ImportError:
        print("✗ tkinter is not available")
        return False
    
    # Check if core modules can be imported
    try:
        from core import ConfigManager, ComponentValidator, CompatibilityChecker
        print("✓ Core modules can be imported")
    except ImportError as e:
        print(f"✗ Core modules import failed: {e}")
        return False
    
    return True

def create_standalone_script():
    """Create a standalone Python script that can be run directly"""
    print("\nCreating standalone script...")
    
    # Read the main application
    with open('main.py', 'r') as f:
        main_content = f.read()
    
    # Read the core module
    with open('core.py', 'r') as f:
        core_content = f.read()
    
    # Create standalone script
    standalone_content = f"""#!/usr/bin/env python3
# PC Builder Application - Standalone Version
# This file contains the complete application

{core_content}

{main_content}
"""
    
    with open('pc_builder_standalone.py', 'w') as f:
        f.write(standalone_content)
    
    # Make it executable
    os.chmod('pc_builder_standalone.py', 0o755)
    
    print("✓ Created pc_builder_standalone.py")
    print("  You can run it with: python3 pc_builder_standalone.py")

def create_build_instructions():
    """Create build instructions for different platforms"""
    print("\n=== BUILD INSTRUCTIONS ===")
    
    instructions = """
# PC Builder Application - Build Instructions

## Method 1: Direct Python Execution
1. Ensure Python 3.7+ is installed
2. Run: python3 pc_builder_standalone.py

## Method 2: Using PyInstaller (Recommended for Windows)
1. Install PyInstaller: pip install pyinstaller
2. Build executable: pyinstaller --onefile --windowed main.py
3. The executable will be in the dist/ folder

## Method 3: Using cx_Freeze
1. Install cx_Freeze: pip install cx_Freeze
2. Create setup.py:
   ```
   from cx_Freeze import setup, Executable
   setup(name="PC Builder", version="1.0",
         executables=[Executable("main.py")])
   ```
3. Build: python setup.py build

## Method 4: Using Auto-py-to-exe (GUI)
1. Install: pip install auto-py-to-exe
2. Run: auto-py-to-exe
3. Select main.py and configure options

## Requirements for Distribution:
- Python 3.7+
- tkinter (usually included with Python)
- config.json (will be created automatically)
- Email configuration in core.py (SMTP_USER, SMTP_PASS)

## Email Configuration:
Before distributing, update the email settings in core.py:
- SMTP_USER: Your Gmail address
- SMTP_PASS: Your Gmail app password

## Testing:
Run the test suite: python3 test_core.py
"""
    
    with open('BUILD_INSTRUCTIONS.md', 'w') as f:
        f.write(instructions)
    
    print("✓ Created BUILD_INSTRUCTIONS.md")

def create_requirements_file():
    """Create requirements.txt file"""
    requirements = """# PC Builder Application Requirements

# Core dependencies (built-in)
# - tkinter (GUI)
# - json (configuration)
# - re (regex for validation)
# - smtplib (email sending)
# - email.message (email formatting)
# - dataclasses (data structures)
# - typing (type hints)

# Optional dependencies for building executables
pyinstaller>=5.0
# OR
cx_Freeze>=6.0
# OR
auto-py-to-exe>=2.0

# For testing
pytest>=7.0
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    
    print("✓ Created requirements.txt")

def main():
    """Main build function"""
    print("PC Builder Application - Build Script")
    print("=" * 40)
    
    if not check_dependencies():
        print("\n❌ Dependencies check failed. Please install required packages.")
        return
    
    create_standalone_script()
    create_build_instructions()
    create_requirements_file()
    
    print("\n✅ Build preparation completed!")
    print("\nNext steps:")
    print("1. Run: python3 pc_builder_standalone.py")
    print("2. Or follow instructions in BUILD_INSTRUCTIONS.md")
    print("3. Test the application: python3 test_core.py")

if __name__ == '__main__':
    main()