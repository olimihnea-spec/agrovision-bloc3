@echo off
title AGROVISION API Server
cd /d "G:\CLAUDE CODE INSTRUIRE VOL II 90 ZILE STREAMLIT ISI YOLO\Bloc3_YOLOv8\yolo_app"
"G:\CLAUDE CODE INSTRUIRE\.venv\Scripts\python.exe" -m uvicorn api:app --reload --port 8000
pause
