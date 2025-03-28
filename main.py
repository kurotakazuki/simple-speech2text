import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import queue
import threading
import json
import sys
import tkinter.font as tkFont

MODEL_PATH = "vosk-model-small-ja-0.22"
DEFAULT_INPUT_DEVICE = "microphone"

q = queue.Queue()


class SpeechApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎤 音声認識GUI - 日本語 Vosk")

        root.attributes("-zoomed", True)

        jp_font = tkFont.Font(family="Noto Sans CJK JP", size=20)
        self.root.option_add("*Font", jp_font)
        jp_font_xl = tkFont.Font(family="Noto Sans CJK JP", size=40)
        self.root.option_add("*Font", jp_font_xl)

        tk.Label(root, text="🎧 入力デバイスを選択", font=jp_font).pack(pady=10)
        self.device_var = tk.StringVar()
        self.device_box = ttk.Combobox(
            root, textvariable=self.device_var, width=80, font=jp_font
        )
        self.device_box.pack(pady=10)

        self.start_btn = tk.Button(
            root, text="▶ 音声認識開始", command=self.start_recognition, font=jp_font
        )
        self.start_btn.pack(pady=20)
        self.stop_btn = tk.Button(
            root,
            text="■ 停止",
            command=self.stop_recognition,
            state=tk.DISABLED,
            font=jp_font,
        )
        self.stop_btn.pack(pady=10)

        self.log_area = scrolledtext.ScrolledText(
            root, width=100, height=15, font=jp_font_xl
        )
        self.log_area.pack(padx=10, pady=20)

        self.running = False
        self.stream = None
        self.model = Model(MODEL_PATH)
        self.recognizer = KaldiRecognizer(self.model, 16000)

        self.devices = []
        self.previous_log = ""  # 直前のログを保存

        self.default_input_device_id = None

        self.populate_devices()

    def populate_devices(self):
        self.devices = sd.query_devices()
        for idx, dev in enumerate(self.devices):
            if DEFAULT_INPUT_DEVICE in dev["name"]:
                self.default_input_device_id = idx
                break
        input_devices = [
            f"{idx}: {dev['name']}"
            for idx, dev in enumerate(self.devices)
            if dev["max_input_channels"] > 0
        ]
        self.device_box["values"] = input_devices
        if input_devices:
            self.device_box.current(0)

    def audio_callback(self, indata, frames, time, status):
        if status:
            self.log(f"⚠️ Audio Status: {status}")
        q.put(bytes(indata))

    def start_recognition(self):
        if not self.device_var.get() and self.default_input_device_id is None:
            messagebox.showwarning("デバイス未選択", "入力デバイスを選択してください")
            return
        if self.default_input_device_id is not None:
            device_index = self.default_input_device_id
        else:
            device_index = int(self.device_var.get().split(":")[0])
        samplerate = self.devices[device_index]["default_samplerate"]
        self.recognizer = KaldiRecognizer(self.model, samplerate)
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.log("🎙 音声認識を開始しました")

        def recognize():
            with sd.RawInputStream(
                samplerate=samplerate,
                blocksize=8000,
                dtype="int16",
                channels=1,
                callback=self.audio_callback,
                device=device_index,
            ):
                while self.running:
                    data = q.get()
                    if self.recognizer.AcceptWaveform(data):
                        result = json.loads(self.recognizer.Result())
                        self.log(f"✔️ 認識結果: {result.get('text', '')}")
                    else:
                        partial = json.loads(self.recognizer.PartialResult())
                        self.log(f"⏳ 中間結果: {partial.get('partial', '')}")

        threading.Thread(target=recognize, daemon=True).start()

    def stop_recognition(self):
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("🛑 音声認識を停止しました")

    def log(self, message):
        if message == "⏳ 中間結果: " or message == "✔️ 認識結果: ":
            return

        self.log_area.delete("1.0", tk.END)

        if self.previous_log:
            self.log_area.insert(tk.END, self.previous_log + "\n")

        self.log_area.insert(tk.END, message + "\n")
        self.log_area.yview(tk.END)

        if message.startswith("✔️"):
            self.previous_log = message


if __name__ == "__main__":
    root = tk.Tk()
    app = SpeechApp(root)
    root.mainloop()
