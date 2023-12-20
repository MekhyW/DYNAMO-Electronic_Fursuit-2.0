@echo off

:: Update the "Eye-Graphics" repository
cd "C:\Users\LattePanda\Documents\GitHub\Eye-Graphics"
git pull
cd "..\"

:: Update the "Eye-Graphics" repository
cd "DYNAMO-Electronic_Fursuit-2.0"
git pull

:: Start Voicemod
start "" "C:\Program Files\Voicemod Desktop\VoicemodDesktop.exe"

:: Start Eye-Graphics.exe
start "" "C:\Users\LattePanda\Documents\GitHub\Eye-Graphics\Eye-Graphics.exe"

:: Start DYNAMO.py
cd "Main software"
python DYNAMO.py
