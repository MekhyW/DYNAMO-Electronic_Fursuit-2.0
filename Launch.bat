@echo off

:: Update the "Eye-Graphics" repository
cd "C:\Users\LattePanda\Documents\GitHub\Eye-Graphics"
git pull || echo Git pull failed
cd "..\"

:: Update the "Eye-Graphics" repository
cd "DYNAMO-Electronic_Fursuit-2.0"
git pull || echo Git pull failed

:: Start Voicemod
start "" "C:\Program Files\Voicemod Desktop\VoicemodDesktop.exe" || echo Voicemod failed to start
python voicemod-autologin.py || echo Voicemod autologin script failed

:: Start Eye-Graphics.exe
start "" "C:\Users\LattePanda\Documents\GitHub\Eye-Graphics\Eye-Graphics.exe" || echo Eye-Graphics failed to start

:: Start DYNAMO.py
cd "Main software"
python DYNAMO.py || echo DYNAMO.py failed to start

:: Pause at the end
pause