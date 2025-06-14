@echo off
python app.py
if errorlevel 1 (
    echo Errore durante l'esecuzione di app.py
    pause
)
pause