@echo off
echo ================================================================================
echo 🚀 RFQ STREAMLIT - QUICK START
echo ================================================================================
echo.

echo 📍 Current directory: %CD%
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo ❌ Virtual environment not found!
    echo.
    echo Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created!
    echo.
)

echo ✅ Activating virtual environment...
call venv\Scripts\activate
echo.

echo 📦 Installing/updating dependencies...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo ✅ Dependencies installed!
echo.

echo ================================================================================
echo 🎉 STARTING STREAMLIT APP
echo ================================================================================
echo.
echo App will open in your browser at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the app
echo ================================================================================
echo.

streamlit run app.py

pause
