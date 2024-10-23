# DYNAMO

Improved modular computing platform for wearable costumes, with animatronic support, facial/eye tracking, sound processing and more

## Overview

Traditional industry-standard mascot and full-body character suits, although fascinating, face severe limitations regarding expressiveness. These limitations are contoured by either resorting to exhausting body acting skills, or the use of very complex moving parts which require expert handlers, are difficult to transport and assemble, and often cannot be used outside of controlled environments.

The Dynamo project addresses these challenges by introducing an innovative platform for full-body mascot and character suits. Its primary goal is to bring characters to life in real, uncontrolled scenarios by enabling autonomous operation without the need for an external operator. 

This is made possible by combining the following key features:

1. Modular Design: The system consists of two main expandable components - a specially designed mask and a component box worn inside a backpack, connected via a wire-joining "vertical spine" structure
2. Advanced Mask Components: The mask incorporates displays, a camera, microphone, servos, and other relevant peripherals to create lifelike expressions and interactions
3. Powerful Processing Unit: A Lattepanda Delta 3 central processing unit housed in the backpack component box serves as the brain of the system
4. Self-Contained Power: Batteries within the component box ensure portability and extended operation
5. Facial/eye-tracking: Custom pipeline for realtime mapping of the wearers gaze and facial expression, which is mirrored on the displayed eyes
6. Audio Processing: A dedicated speaker enables clear voice communication + realtime and non-realtime sound effects
7. Self-Hosted Control Bot: Custom control and debugging interface remotely accessible by the wearer or a third party
8. Assistant Intelligence: Extra layer of interactivity and autonomy with the use of generative AI capable of executing commands and generating responses

## Directory Structure

```
├───AVR_software
├───CAD
│   ├───Electronics
│   ├───Mechanics
│       └───Component box
│       └───Example head
│       └───Mask
│       └───Hinge
├───Logos
├───Main software
│   ├───resources
├───Planning
└───Test scripts
```

- AVR_software: C++ code for the AVR microcontroller responsible for controlling the servos, fan(s) and LEDs of the suit
- CAD: Design files for the components of the project
- Logos: Logos used in the project
- Main software: Python code for the main software of the project. The 'resources' folder contains the machine learning models and other resources used by the software
- Planning: Diagrams and planning documents
- Test scripts: Some scripts used for testing the project

## Hardware Assembly

![Hardware Diagram](Planning/Hardware.png)

## Software Setup

![Software Diagram](Planning/Software.png)

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

### 6. Clone Repositories to Documents Folder

Clone the project repositories to `C:\Users\LattePanda\Documents\GitHub` folder using the following commands in Git Bash:

```bash
cd C:\Users\LattePanda\Documents\GitHub
git clone https://github.com/MekhyW/DYNAMO-Electronic_Fursuit-2.0
git clone https://github.com/MekhyW/Eye-Graphics
# Optionally, you can also clone the following repository to see the machine vision model training pipeline:
git clone https://github.com/MekhyW/Facial-Emotion-Classification
```

### 7. Install Requirements.txt

Navigate to the project's main directory in Git Bash and install the required Python packages using the following command:

```bash
pip install -r requirements.txt
```

### 8. Provide credentials

Create a `.env` file in the root folder of the project's main repository, with the following contents:

```bash
voicemod_key = "YOUR_VOICEMOD_KEY"
fursuitbot_token = "YOUR_TELEGRAM_BOT_TOKEN"
fursuitbot_ownerID = "YOUR_TELEGRAM_USER_ID"
openai_key = "YOUR_OPENAI_API_KEY"
porcupine_key = "YOUR_PORCUPINE_API_KEY"
```

### 9. AVR_software

Open the `AVR_software/AVR_software.ino` file in the Arduino IDE. Install the following libraries via the Arduino IDE Library Manager (with dependencies):

- FreeRTOS
- Adafruit NeoPixel
- Adafruit BNO055

### 10. Set Launch.bat to Run on Boot

Edit the `Launch.bat` file to run on boot. You can achieve this by placing a shortcut to the batch file in the Windows Startup folder.

### 11. Setup Displays

I use a UDisplay HDMI-USB adapter for the second eye display. Whatever the device, make sure that it´s firmware is up to date and set to autorun.
Set the second display to be an extended display.

### 12. Setup 4G Module

To allow the suit to connect to the internet outside of WiFi range, I use a 4G LTE Wifi USB modem with a SIM card. Make sure that the LattePanda recognizes the modem and remembers the connection!

In the case of my modem, the IP address is 192.168.100.1, the default username and password are admin/admin, and the default WiFi access point password is 1234567890. Change these settings to your own for security reasons.

Make sure that the Access Point Name (APN) is set to ONLY ipv4. This is important since Telegram servers do not support ipv6 and will not work if the APN is set to ipv4/ipv6. Also, it should contain the username and password of the SIM card, as expected by the carrier.

If possible, use 4G/3G mode instead of just 4G. This is because 4G mode can be unstable in some areas and the system will not be able to connect to the internet.


## Preparations before each use

1) Recharge the batteries of the system
2) Check if SIM card has enough data, if not, recharge it
3) Make sure all hardware is connected
4) Open Telegram on phone or have a friend use the bot for control