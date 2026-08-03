# HJAI Assistant Platform

Welcome to the **HJAI Assistant Platform**! This repository contains a comprehensive suite of applications designed to provide intelligent assistance across various modalities.

## Project Structure

The platform is divided into three main components:

- **`backend/`**: A robust FastAPI backend that handles the core AI operations, memory management, and integrations. It utilizes PostgreSQL for relational data, Redis for caching/queuing, ChromaDB as a vector database, and Celery for asynchronous background tasks. It also interfaces with a local Ollama instance for LLM capabilities.
- **`frontend/`**: A modern Next.js web application built with React, TypeScript, and Tailwind CSS v4.
- **`copilot_app/`**: A PyQt6 desktop application for Windows. This "invisible to screen share" assistant captures system audio, transcribes it using Whisper, and provides an overlaid, non-intrusive chat interface powered by local AI.

## Requirements

- [Docker](https://www.docker.com/) & Docker Compose
- Node.js (for frontend development)
- Python 3.11+ (for backend and copilot_app development)
- [Ollama](https://ollama.com/) running locally for the AI engine.

## Getting Started

The main platform services (Frontend, Backend, Databases, and Task Queues) can be spun up using Docker Compose.

```bash
docker-compose up --build
```

This will launch:
- **Frontend (Next.js)** on `http://localhost:3000`
- **Backend (FastAPI)** on `http://localhost:8000`
- **PostgreSQL** database on port `5432`
- **Redis** cache on port `6379`
- **ChromaDB** vector database on port `8001`
- **Celery Worker** and **Beat Scheduler** background processes

### Running the Copilot App

The Copilot App is a standalone desktop application that communicates with the local AI setup.

1. Navigate to the `copilot_app` directory:
   ```bash
   cd copilot_app
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```
   *Alternatively, you can use `start_copilot.bat` or `start_copilot_hidden.vbs` on Windows to launch it without a command prompt window.*

## Features

- **Multi-Modal API**: The backend supports chat, memory, documents, vision, voice, and intelligent agent workflows.
- **Invisible Desktop Assistant**: The Copilot app stays hidden from screen sharing tools (Zoom, Teams, Google Meet, etc.), captures system audio for real-time transcription, and provides instant AI assistance without interrupting your workflow.
- **Scalable Architecture**: Uses Celery and Redis to manage heavy, asynchronous workloads like audio processing, background jobs, and model inference.
