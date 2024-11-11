:: Install Python dependencies
pip install -r requirements.txt

:: Compile and upload the AVR software
cd "AVR_software"
set "ARDUINO_CLI=.\arduino-cli.exe"
"%ARDUINO_CLI%" core update-index
"%ARDUINO_CLI%" lib update-index
"%ARDUINO_CLI%" core install arduino:avr
"%ARDUINO_CLI%" lib install "Adafruit NeoPixel" "Adafruit BNO055" FreeRTOS Servo
"%ARDUINO_CLI%" compile --fqbn arduino:avr:leonardo AVR_software.ino
"%ARDUINO_CLI%" upload -p COM3 --fqbn arduino:avr:leonardo AVR_software.ino
cd "..\"

:: Set Launch.bat to run on startup
copy /Y "Launch.bat" "C:\Users\LattePanda\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"

:: Clone the auxiliary repositories
cd C:\Users\LattePanda\Documents\GitHub
git clone https://github.com/MekhyW/Eye-Graphics
git clone https://github.com/MekhyW/Facial-Emotion-Classification

:: Install Chocolatey and FFmpeg
@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command " [System.Net.ServicePointManager]::SecurityProtocol = 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
choco install ffmpeg

:: Pause at the end
pause
