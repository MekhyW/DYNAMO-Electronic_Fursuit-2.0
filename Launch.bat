@echo off

:: Update the "Eye-Graphics" repository
cd "C:\Users\LattePanda\Documents\GitHub\Eye-Graphics"
git pull || echo Git pull failed
cd "..\"

:: Update the "DYNAMO-Electronic_Fursuit-2.0" repository
cd "DYNAMO-Electronic_Fursuit-2.0"
git pull || echo Git pull failed

:: Minimize the command prompt window
powershell -window minimized -command ""

:: Start Eye-Graphics.exe
start "" "C:\Users\LattePanda\Documents\GitHub\Eye-Graphics\Build\Eye-Graphics.exe" || echo Eye-Graphics failed to start

:: Start DYNAMO.py
cd "Main software"
python DYNAMO.py || echo DYNAMO.py failed to start

:: Pause at the end
pause
