# 🈹 JSON Translator – OpenAI / Amazon

A desktop application to translate structured JSON content into multiple languages using **OpenAI** or **Amazon Translate**.  
It supports both **flat** and **deeply nested** JSON structures while preserving the hierarchy and formatting.  
The tool provides **Blog** and **Non-Blog** modes, easy **language management**, and a **clean Tkinter GUI** interface.

---

## 🚀 Features

### 🌍 Multi-Language Translation
- Translate JSON content into **multiple target languages** in a single run.  
- All target translations (e.g., `ar`, `fr`, `es`) are merged into one output JSON file.  
- Manage target languages dynamically through a popup window.

**Default languages:** Arabic (`ar`), French (`fr`), Spanish (`es`)  
Additional languages can be added anytime.

---

### 🧩 Deep JSON Handling
- Handles **nested** structures such as:
  - `title`, `description`, and localized text blocks.
  - `additionalContent` arrays and multilingual nodes.
- Maintains proper language separation and prevents overwriting of existing data.
- Removes empty or invalid text fields automatically before translation.

---

### ⚙️ Dual Translation Engines
- **OpenAI Engine:** Uses GPT-based translation for natural, human-like phrasing.  
- **Amazon Translate:** Uses AWS neural translation for structured and enterprise-safe output.
- Built-in key/credential verification for both engines.

---

### 🧠 Two Operating Modes
- **Blog Mode:**  
  Creates a separate translated file for each language (ideal for localized blog/article exports).
  
- **Non-Blog Mode:**  
  Produces a **single JSON file** containing all translated languages (e.g., `en`, `ar`, `fr`, `es`).

Each mode automatically organizes outputs:
```
/YourFolder/
├── Blog/
│   ├── file_ar.json
│   ├── file_fr.json
│   └── file_es.json
└── Non-Blog/
    └── file_translated.json
```

---

### 🪟 Clean, Intuitive GUI
- Built with **Tkinter** for a lightweight desktop experience.  
- Key components:
  - File selector for input JSON.
  - Language management popup.
  - Translation engine selector (OpenAI / Amazon).
  - Progress bar and live status messages.
  - Start / Cancel translation control.

---

### 🔒 Safe Data Handling
- The original JSON is **never modified**.  
- Translations are applied to a deep copy of the structure.  
- Results are saved in clearly organized folders (`Blog` / `Non-Blog`).  
- Supports UTF-8 output with proper handling of non-Latin characters (e.g., Arabic, Hindi, Chinese).

---

## 🧰 Installation

### 1️⃣ Clone the repository
```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

### 2️⃣ Install dependencies
```bash
pip install openai boto3 cryptography requests
```

> 💡 **Tkinter** comes pre-installed with most Python distributions.  
> If not available:
> ```bash
> sudo apt install python3-tk  # (Linux)
> ```

---

## ▶️ Usage

Run the main GUI script:

```bash
python translator_main_gui.py
```

1. **Select a JSON file** containing your source language content (e.g., English).  
2. Choose **Source Language** (default: `en`).  
3. Add or remove **Target Languages** from the “Manage Languages” popup.  
4. Pick your **Translation Engine** — OpenAI or Amazon.  
5. Choose mode:  
   - Blog Mode ✅ (separate per-language files)  
   - Non-Blog Mode 🌐 (all languages in one file)  
6. Click **Start Translation** — progress and messages appear in real time.

---

## 📁 Output Examples

### ✅ Non-Blog Mode
Output file:  
`/Non-Blog/data_translated.json`
```json
{
  "title": {
    "en": "Welcome",
    "ar": "مرحبا",
    "fr": "Bienvenue",
    "es": "Bienvenido"
  }
}
```

### ✅ Blog Mode
Folder `/Blog/` contains:
```
data_ar.json
data_fr.json
data_es.json
```

---

## 🧩 File Structure Overview

```
translator_main_gui.py         # GUI entry point
translator_gui_functions.py    # File handling, threading, and progress logic
translator_logic.py            # Non-Blog translation logic (multi-language merged)
translator_blog_logic.py       # Blog mode logic (per-language export)
translator_lang.py             # Language management and popup UI
translate_openai.py            # OpenAI translation utilities
translate_aws.py               # AWS Translate utilities
```

---

## 🔑 Credentials

### OpenAI
Create a `.env` file or provide your API key via popup:
```
OPENAI_API_KEY=sk-xxxxxxxxxxxx
```

### Amazon Translate
Requires AWS access credentials:
```
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
```

---

## 🧠 Notes
- Supports translation of large, nested JSON structures (like CMS exports, blogs, or apps).
- Automatically skips empty or invalid `text` nodes for Amazon Translate.
- Cleanly handles right-to-left scripts (Arabic, Hebrew) in JSON outputs.
- Translation progress and completion messages are shown in the GUI.

---

## 🪪 License
© 2025 JSON Translator – Human-like Output  
Licensed for personal and professional use under the MIT License.
