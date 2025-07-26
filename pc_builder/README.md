# PC Builder Application

A standalone desktop application for custom PC building with admin and user modes.

## Features
- Admin panel for managing PC components, prices, and destination email address
- User panel for selecting compatible PC components
- Automatic compatibility checks
- Build submission via email

## How to Run
1. Install dependencies: `pip install -r requirements.txt`
2. Run the app: `python main.py`
3. Build standalone exe: `pyinstaller --onefile main.py`