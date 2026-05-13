@echo off
echo ========================================
echo   DEMONSTRATION RAPIDE - ISEC PROJECT
echo ========================================
echo.

echo [1/3] Generation des certificats...
python generate_certs.py
echo.

echo [2/3] Mode demonstration - Visualisation du chiffrement...
echo Appuyez sur ENTREE pour continuer...
pause > nul
python demo_mode.py
echo.

echo [3/3] Transfert avec mode verbose...
echo.
echo Demarrez le serveur dans un autre terminal avec:
echo    python server.py
echo.
echo Puis lancez le client en mode verbose:
echo    python client.py --file test_demo.txt --verbose
echo.
echo Pour capturer avec Wireshark:
echo    wireshark -i Loopback -k -f "tcp port 9000"
echo.

pause
