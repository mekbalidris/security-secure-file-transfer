@echo off
echo ========================================
echo   TEST - VOIR LES FICHIERS CHIFFRES
echo ========================================
echo.

echo [1/3] Creation d'un fichier de test...
echo MESSAGE SECRET ISEC 2026 - Ceci est confidentiel ! > test_secret.txt
echo Fichier cree: test_secret.txt
echo.

echo [2/3] Demarrez le serveur dans un autre terminal avec:
echo    python server.py
echo.
echo Puis appuyez sur ENTREE pour continuer...
pause > nul

echo [3/3] Envoi du fichier...
python client.py --file test_secret.txt
echo.

echo ========================================
echo   VERIFICATION
echo ========================================
echo.
echo Vous devriez maintenant avoir DEUX fichiers dans received_files/:
echo.
dir received_files\test_secret.txt*
echo.

echo Ouvrez les fichiers pour comparer:
echo.
echo 1. Fichier dechiffre (LISIBLE):
echo    notepad received_files\test_secret.txt
echo.
echo 2. Fichier chiffre (ILLISIBLE):
echo    notepad received_files\test_secret.txt.encrypted
echo.

pause
