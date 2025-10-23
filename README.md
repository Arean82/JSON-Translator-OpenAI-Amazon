# JSON Translator – OpenAI / Amazon

A desktop application to translate structured JSON content into multiple languages using **OpenAI** or **Amazon Translate** engines. It supports both flat and deeply nested JSON structures, including complex content blocks, ensuring accurate translations while preserving the JSON hierarchy.

---

## Features

- **Multi-Language Support**
  - Translate JSON content to multiple target languages at once.
  - Manage supported languages via a popup interface.
  - Default languages: Arabic (`ar`), French (`fr`), Spanish (`es`); additional languages can be added.

- **Deep Nested Translation**
  - Handles nested structures including `additionalContent` arrays and text fields in complex JSON trees.
  - Maintains proper mapping between source and target languages to avoid overwriting.

- **Flexible Engine Selection**
  - Choose between **OpenAI** and **Amazon Translate**.
  - Supports API key/credential verification for secure access.

- **User-Friendly GUI**
  - Built with Tkinter for a clean, intuitive interface.
  - Easy file selection, engine choice, and language management.
  - Progress bar and status messages during translation.

- **Safe Data Handling**
  - Original JSON is never overwritten; translations are applied to a deep copy.
  - Translated JSON can be saved to a separate output file.

- **Language Map Integration**
  - ISO code → Language Name mapping for easy identification.
  - Validate and add new languages via popup.

---

## Installation

1. Clone the repository:

```bash
git clone <your-repo-url>
cd <your-repo-folder>
