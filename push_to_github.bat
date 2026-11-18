@echo off
setlocal
set REPO_URL=https://github.com/willieka1/subak-soil.git

echo [1/4] Initializing Git repository...
if not exist ".git" (
    git init
    git branch -M main
)

git remote set-url origin %REPO_URL% 2>nul || git remote add origin %REPO_URL%

echo [2/4] Staging project files...
git add .gitignore requirements.txt vercel.json subak_soil_datasheet.csv subak_soil_scheduler.py app.py api/index.py public/index.html README.md

echo [3/4] Creating release commit...
git commit -m "feat: refactor core CP-SAT scheduler, spatial validation, and dual Streamlit/Vercel UI"

echo [4/4] Pushing to %REPO_URL% (main)...
git push -u origin main --force

echo Done. Repository pushed to https://github.com/willieka1/subak-soil
pause
