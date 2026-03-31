@echo off
REM ============================================
REM INSTALLATION QUICK WINS - SmartCaisse
REM ============================================

echo.
echo ========================================
echo   Installation Quick Wins SmartCaisse
echo ========================================
echo.

REM Etape 1: Installation dependances
echo [1/5] Installation des nouvelles dependances...
pip install Flask-Talisman==1.1.0 Flask-Limiter==3.5.0 APScheduler==3.10.4
if errorlevel 1 (
    echo ERREUR: Installation des dependances echouee
    pause
    exit /b 1
)
echo [OK] Dependances installees
echo.

REM Etape 2: Creer dossier logs
echo [2/5] Creation du dossier logs...
if not exist logs mkdir logs
echo [OK] Dossier logs cree
echo.

REM Etape 3: Generer SECRET_KEY
echo [3/5] Generation de la SECRET_KEY...
python -c "import secrets; key=secrets.token_hex(32); print('\nVotre SECRET_KEY:'); print(key); print('\nCopiez cette cle pour l etape suivante!')" > temp_key.txt
type temp_key.txt
echo.

REM Etape 4: Creer .env
echo [4/5] Configuration du fichier .env...
if exist .env (
    echo ATTENTION: Le fichier .env existe deja!
    echo Sauvegarde en .env.backup
    copy .env .env.backup >nul
)
copy .env.example .env >nul
echo [OK] Fichier .env cree depuis .env.example
echo.
echo IMPORTANT: Editez maintenant le fichier .env et ajoutez votre SECRET_KEY
echo La cle se trouve dans temp_key.txt
echo.

REM Etape 5: Instructions test
echo [5/5] Pret pour les tests!
echo.
echo ========================================
echo   INSTALLATION TERMINEE
echo ========================================
echo.
echo PROCHAINES ETAPES:
echo.
echo 1. Ouvrez le fichier .env dans un editeur
echo 2. Remplacez la ligne SECRET_KEY par la cle generee (dans temp_key.txt)
echo 3. Lancez: python run.py
echo 4. Verifiez logs\smartcaisse.log
echo.
echo Fichiers crees:
echo   - logs\ (dossier)
echo   - .env (configuration)
echo   - temp_key.txt (cle secrete - A SUPPRIMER apres)
echo.

pause
