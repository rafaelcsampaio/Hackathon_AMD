# AMD Intelligent Pair Programmer (AIPP)

An autonomous multimodal assistant that sees your workspace, understands your voice commands, and injects code directly into your project. Built for the **AMD Developer Hackathon**.

## 🚀 Overview

AIPP is more than a chatbot; it is a "Jarvis-like" co-pilot for software engineers. By leveraging the **Qwen-VL-30B** multimodal model (via Fireworks AI) and hardware-accelerated sensory modules, AIPP can:
- **See:** Observe your IDE and terminal in real-time.
- **Hear:** Process continuous voice commands with low-latency Whisper-based STT.
- **Speak:** Provide fluid vocal feedback using a zero-latency Producer-Consumer audio pipeline.
- **Act:** Inject code directly into your files at specific lines or copy snippets to your clipboard.

---

## 🏗️ Architecture

The system is built on a highly modular, multithreaded architecture designed for stability and responsiveness:

- **AudioListener (The Ear):** Continuous background listening with Voice Activity Detection (VAD). Includes "Jarvis-mode" interruption—when you speak, the AI stops talking to listen.
- **VisionEngine (The Eye):** Captures the visual context of the workspace to provide the LLM with eyes on your code, terminal errors, and UI.
- **AIBrain (The Mind):** Uses **Qwen-VL-30B** to reason over both visual and textual inputs.
- **SpeechEngine (The Voice):** A concurrent pipeline that downloads and plays audio chunks sequentially, ensuring no lag between the AI's thought and its speech.
- **CodeInjector (The Hand):** Executes physical actions like writing code to disk or interacting with the clipboard.

---

## 🛠️ Tech Stack

- **LLM:** Qwen-VL-30B (Multimodal) via Fireworks AI.
- **Speech-to-Text:** OpenAI Whisper (Base Model).
- **Text-to-Speech:** Edge-TTS (Neural voices).
- **Audio Processing:** Pygame, SoundDevice, SciPy.
- **Vision:** PyAutoGUI, PIL.
- **Language:** Python 3.11+.

---

## 🔧 Installation & Setup

1. **Download the project:**
   Download the `AIPP_Source_Code.zip` file from the "Files" tab in this Hugging Face Space and extract it to a folder on your local machine.
   
2.**Setup Virtual Environment:**

python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

3.**Install Dependencies:**

pip install -r requirements.txt

4.**Environment Variables:**
Create a .env file with your Fireworks AI API Key:

FIREWORKS_API_KEY=your_key_here

5**Run:**

python main.py

## 👤 Team
Rafael Campos Sampaio - Lead Software Engineer & AI Architect.

Software Engineering Student at UCSAL | Technical Degree in Systems Development (SENAI CIMATEC).

## 📄 License
This project is part of the AMD Developer Hackathon 2026.