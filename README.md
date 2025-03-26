
# Simple Speech To Text

## Install

Python: 3.10.12

```sh
sudo apt install unzip
sudo apt install python3-pyaudio
sudo apt install python3-tk
sudo apt install fonts-noto-cjk fonts-takao

python -m venv venv
source venv/bin/activate


# pip install vosk sounddevice tkinter
pip install -r requirements.txt

curl -L -o vosk-model-small-ja-0.22.zip https://alphacephei.com/vosk/models/vosk-model-small-ja-0.22.zip
unzip vosk-model-small-ja-0.22.zip

python main.py

```