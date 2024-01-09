# DYNAMO

TBW

# Directory Structure

TBW

# How it Works

TBW

# Software Setup

To setup the project software on a LattePanda Delta 3 board, follow the steps below for required environment and configurations. It should be running Windows 10 and have a stable internet connection.
I also recommend updating to the latest update of Windows 10, and removing any bloat software from the system (such as Cortana, Office 365, etc).

### 1. Install Git Bash

You can download it from [Git for Windows](https://gitforwindows.org/).
Optionally, you can also install [GitHub Desktop](https://desktop.github.com/) for a GUI interface.

### 2. Install Python 3.11

Download and install Python 3.11 from the official [Python website](https://www.python.org/). During installation, make sure to check the option to add Python to the system PATH and include pip.

### 3. Install FFMPEG

Open the Windows Command Shell with administrator privileges and run the following commands:

```bash
@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command " [System.Net.ServicePointManager]::SecurityProtocol = 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
choco install ffmpeg
```

### 4. Install Voicemod

Download and install Voicemod from the official [Voicemod website](https://www.voicemod.net/). Install it in the `C:\Program Files` directory. Then log in to your Voicemod account and activate the Pro license if not already activated.

DO NOT use the same account as another device, as it will log out the other device or vice versa!!

### 5. Configure Audio Settings in Voicemod

Open Voicemod and configure the audio settings, including reduction (I recommend leaving at a high value, like 80%) and set it to update without asking.

The file `voidemod-presets.vs2` contains the presets used for the project. You can import it into Voicemod to use the same settings.

### 6. Setup Displays

I use a UDisplay HDMI-USB adapter for the second eye display. Whatever the device, make sure that it´s firmware is up to date and set to autorun.
Set the second display to be an extended display.

### 7. Clone Repositories to Documents Folder

Clone the project repositories to `C:\Users\LattePanda\Documents\GitHub` folder using the following commands in Git Bash:

```bash
cd C:\Users\LattePanda\Documents\GitHub
git clone https://github.com/MekhyW/DYNAMO-Electronic_Fursuit-2.0
git clone https://github.com/MekhyW/Eye-Graphics
# Optionally, you can also clone the following repository to see the machine vision model training pipeline:
git clone https://github.com/MekhyW/Facial-Emotion-Classification
```

### 8. Install Requirements.txt

Navigate to the project's main directory in Git Bash and install the required Python packages using the following command:

```bash
pip install -r requirements.txt
```

### 9. Provide credentials.json

Create a `credentials.json` file in the `Main software` folder of the project's main repository, with the following contents:

```json
{
    "voicemod_key": "YOUR_VOICEMOD_KEY",
    "fursuitbot_token": "TELEGRAM_BOT_KEY",
    "fursuitbot_ownerID": "YOUR_TELEGRAM_ID",
    "openai_key": "OPENAI_API_KEY",
    "porcupine_key": "PORCUPINE_API_KEY"
}
```

### 10. AVR_software

Open the `AVR_software/AVR_software.ino` file in the Arduino IDE. Install the following libraries via the Arduino IDE Library Manager (with dependencies):

- FreeRTOS
- Adafruit NeoPixel
- Adafruit BNO055

Upload the code to the Arduino Leonardo device inside of the Lattepanda.

### 11. Set Launch.bat to Run on Boot

Edit the `Launch.bat` file to run on boot. You can achieve this by placing a shortcut to the batch file in the Windows Startup folder.


# Preparations before each use

1) Recharge the batteries of the system
2) Check if SIM card has enough data, if not, recharge it
3) Test hardware connections and software functionality