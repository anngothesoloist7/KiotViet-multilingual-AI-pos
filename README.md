# 🎙️ Knote Voice POS: Next-Gen MVP

> **Developed as part of the Internship Program at [KiotViet Technology Corporation](https://www.kiotviet.vn/).**

## 📖 Overview

This project is an experimental **Voice-Ordering Engine** designed to upgrade the existing voice feature within the **Knote Ecosystem**.

Addressing the limitations of the previously launched version (which struggled with background noise and rigid keywords), this MVP leverages **OpenAI Whisper** and **GPT-4o-mini** to deliver a robust, noise-canceling, and context-aware ordering experience.

### 🖼️ System Architecture
![System Architecture](assets/architecture.png)

## 🚀 Key Improvements

* **Superior Accuracy:** Replaced unstable client-side recognition with **OpenAI Whisper**, ensuring high accuracy even in noisy kitchen environments.
* **Smart Logic (GPT-4o-mini):** Decouples "Hearing" from "Thinking". The system understands complex intents, corrections (*"Remove the burger, add pizza"*), and attributes without requiring rigid commands.
* **Multilingual Support:** Seamlessly handles **Vietnamese**, **English**, and mixed "Vinglish" inputs natural to local users.
* **Strict JSON Output:** Guarantees deterministic data structure for instant POS integration.

### 📱 Demo Preview
![Live Demo](assets/demo_screenshot.png)

## 🛠️ Tech Stack

* **Backend:** Python (Flask)
* **AI Models:** OpenAI Whisper (STT) + GPT-4o-mini (NLP)
* **Frontend:** HTML5, TailwindCSS, Vanilla JS

---
*© KiotViet Corp.*
