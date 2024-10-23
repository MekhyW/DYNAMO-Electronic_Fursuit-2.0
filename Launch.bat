@echo off

:: Update the "Eye-Graphics" repository
cd "C:\Users\LattePanda\Documents\GitHub\Eye-Graphics"
git pull || echo Git pull failed
cd "..\"

:: Update the "DYNAMO-Electronic_Fursuit-2.0" repository
cd "DYNAMO-Electronic_Fursuit-2.0"
git pull || echo Git pull failed

:: Upload AVR code to the LattePanda's Arduino
cd "AVR_software"
set "ARDUINO_CLI=.\arduino-cli.exe"
"%ARDUINO_CLI%" core update-index
if %errorlevel% equ 0 (
    "%ARDUINO_CLI%" compile --fqbn arduino:avr:leonardo AVR_software.ino || echo Arduino CLI failed to compile
    "%ARDUINO_CLI%" upload -p COM3 --fqbn arduino:avr:leonardo AVR_software.ino || echo Arduino CLI failed to upload
) else (
    echo Arduino CLI failed to update
)
cd "..\"

:: Start Eye-Graphics.exe
start "" "C:\Users\LattePanda\Documents\GitHub\Eye-Graphics\Build\Eye-Graphics.exe" || echo Eye-Graphics failed to start

:: Start DYNAMO.py
cd "Main software"
python DYNAMO.py || echo DYNAMO.py failed to start

:: Pause at the end
pause