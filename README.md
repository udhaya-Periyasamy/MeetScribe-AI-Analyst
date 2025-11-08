# MeetScribe AI Analyst 🎙️

**Tagline:** MeetScribe turns your hour-long meeting into a one-minute, actionable report.

## 🚀 Elevator Pitch

We all waste hours in meetings, but the real problem is that current note-taking tools are "blind." They just transcribe audio, giving you a wall of text while completely missing what's on the slides.

MeetScribe is an AI meeting analyst that uses Gemini's powerful video analysis. It doesn't just *listen* to your meeting; it *watches* it.

It reads the text from your presentation slides, analyzes your team's sentiment from their tone of voice, and extracts every single action item. It then delivers a one-page PDF report with the summary, sentiment, and a "to-do" list.

## 💡 What it Does
This is an all-in-one AI Productivity and Learning Suite that centralizes your workflow. It features:

* **MeetScribe (Video Analyst):** Upload a meeting video (`.mp4`), and the AI "watches" it, reads the slides, and analyzes the audio to generate an instant, actionable **PDF report**.
* **Image Analyzer:** Upload any image—like a complex diagram or chart—and get a detailed explanation.
* **Stream Partner (Language Tutor):** A conversational AI chat to practice speaking and writing in a new language.
* **AI Chat:** A general-purpose AI assistant for quick questions and brainstorming.

## 💻 Tech Stack

### Backend (The "Brain")
* **Language:** Python
* **Web Server:** Flask
* **PDF Generation:** fpdf2

### Frontend (The "Face")
* **Structure:** HTML
* **Styling:** CSS
* **Interactivity:** JavaScript

### Core AI (The "Magic")
* **AI Service:** Google Gemini API
* **Model:** `gemini-2.5-flash` (for multimodal video, image, and text analysis)
* **API Library:** `google-generative-ai` (Python SDK)

---

*This project was built for the Aarambh Hackathon.*