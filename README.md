# 🧭 CareerCompass AI

**Multi-Step Reasoning Agent for Intelligent Career Guidance & Live Market Intelligence**

[![Microsoft Azure](https://img.shields.io/badge/Azure-0078D4?style=flat&logo=microsoft-azure)](https://azure.microsoft.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat&logo=python)](https://www.python.org)
[![React](https://img.shields.io/badge/React-18+-blue?style=flat&logo=react)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#-key-features)
- [Architecture](#%EF%B8%8F-architecture)
- [Quick Start](#-quick-start)
- [Technologies](#-technologies)
- [Project Structure](#-project-structure)
- [How It Works](#-how-it-works)
- [Performance & Metrics](#-performance--metrics)
- [Contributing](#-contributing)
- [Author](#-author)

---

## 🎯 Overview

**CareerCompass AI** is an intelligent, multi-step reasoning career advisor built for the **Microsoft Agents League Hackathon 2026 (Reasoning Agents Track)**. Leveraging **Azure AI Foundry**, **Azure OpenAI (GPT-4.1-mini)**, and **Azure AI Search**, CareerCompass acts as an autonomous agent that guides students and professionals through their career journey.

Unlike typical conversational chatbots, CareerCompass follows a transparent, **6-step architectural reasoning process** to analyze skills, search a vetted career knowledge base, identify gaps, construct detailed roadmap timelines, fetch **live market demand metrics from real job search APIs**, and provide judge-ready PDF/CSV deliverables.

---

## ✨ Key Features

### 🧠 6-Step Transparent Reasoning Chain
Every phase of the agent's analytical thinking is visual and displayed to the user in real-time:
1. **Profile Analysis** — Extracts core skills, goals, education, and experience from free-text input.
2. **Career Path Search** — Queries Azure AI Search (indexed O*NET database) to find the best career alignments.
3. **Skills Gap Analysis** — Systematically determines missing skills and knowledge areas for target roles.
4. **Opportunity Ranking** — Scores careers (1-10) using multi-criteria fit, growth, and entry effort.
5. **Roadmap Creation** — Generates a structured 30-60-90 day timeline with phase-based actions.
6. **Action Plan Synthesis** — Compiles a complete, formatted strategy with premium, non-generic project ideas and resources.

### 📊 Live Market Demand Intelligence
No hardcoded placeholders. When requested, the backend performs live API searches for analyzed skills across multiple major platforms:
- **Himalayas Remote Jobs API** (Server-side search of over 98,000 global opportunities)
- **RemoteOK Public API**
- **Remotive Jobs API**
- **Arbeitnow API**
- **GitHub Search API** (to measure open-source skill adoption)
- Calculates a real-time **Demand Score (0-100)**, **Demand Band (High/Moderate/Emerging/Watch)**, shows total matching live jobs, and showcases sample active job openings.

### ⚖️ JSON-Driven Career Comparison UI
A dedicated career comparison module that lets users input two paths side-by-side. The backend generates a strict JSON payload, rendering a custom grid detailing:
- Required Skills
- Time to Enter
- Growth & Salary Potential
- Job Market Outlook
- Work-Life Balance
- Best Fit For Profile
- An AI Verdict recommendation

### 📥 Judge-Ready Export Deliverables
- **Detailed Career Strategy (PDF)** — Formatted using `reportlab` with clean typography, tables, and full reasoning logs.
- **Skills Checklist (CSV)** — Generates an interactive spreadsheet containing action items and skills gap trackers.

### 🎨 Premium Glassmorphic UI
- Responsive, dark-themed layout built with React.
- Micro-animations: profiling pulses, loading spinners displaying current reasoning state, gradient hover states, and smooth card transitions.
- Interactive elements using `lucide-react` icons and fully-rendered Markdown support.

---

## 🏗️ Architecture

```
                       ┌────────────────────────────────────────────────┐
                       │               CareerCompass AI                 │
                       │                                                │
                       │   ┌────────────────────────────────────────┐   │
                       │   │   React Frontend (localhost:3000)      │   │
                       │   │   - Glassmorphic UI & animations       │   │
                       │   │   - Step-by-step progress tracking     │   │
                       │   │   - Compare UI, export & feedback      │   │
                       │   └────────────────────────────────────────┘   │
                       │                       │                        │
                       │                       ▼                        │
                       │   ┌────────────────────────────────────────┐   │
                       │   │   FastAPI Backend (localhost:8000)     │   │
                       │   │   - /analyze: Reasoning pipeline       │   │
                       │   │   - /market-demand: Live API checks    │   │
                       │   │   - /compare: JSON career comparison   │   │
                       │   │   - /export-pdf & /export-skills-check │   │
                       │   └────────────────────────────────────────┘   │
                       │                       │                        │
                       │                       ▼                        │
                       │   ┌────────────────────────────────────────┐   │
                       │   │   Azure OpenAI (GPT-4.1-mini)          │   │
                       │   │   - Core reasoning orchestrator        │   │
                       │   │   - Multi-turn adaptive feedback       │   │
                       │   └────────────────────────────────────────┘   │
                       │                 ↙            ↘                 │
                       │   ┌───────────────────┐    ┌─────────────────┐ │
                       │   │ Azure AI Search   │    │ Live Job APIs   │ │
                       │   │ (O*NET Knowledge) │    │ (Himalayas, etc)│ │
                       │   └───────────────────┘    └─────────────────┘ │
                       └────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- An Azure account with an Azure AI Foundry project and an Azure AI Search resource.

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/careercompass-ai.git
cd careercompass-ai
```

### 2. Set Up Virtual Environment & Dependencies
```bash
# Create and activate python virtual environment
python -m venv venv
# On Windows (PowerShell):
venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory and insert your Azure connection parameters:
```env
PROJECT_ENDPOINT=https://your-ai-foundry-project-endpoint...
PROJECT_KEY=your-project-key...
AZURE_SEARCH_ENDPOINT=https://your-search-service-endpoint...
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini
```
*(Get `PROJECT_ENDPOINT` and `PROJECT_KEY` from your Azure AI Foundry dashboard; `AZURE_SEARCH_ENDPOINT` from your Azure Portal AI Search overview).*

### 4. Initialize Knowledge Base
This step processes the career index and uploads occupation profiles (O*NET + ESCO skills) directly into Azure AI Search.
```bash
python setup_knowledge.py
```

### 5. Run the Backend API Server
```bash
uvicorn main:app --reload
# API documentation available at http://localhost:8000/docs
```

### 6. Set Up & Run React Frontend
In a new terminal shell:
```bash
cd frontend
npm install
npm start
# Runs web application on http://localhost:3000
```

---

## 💻 Technologies

### Backend
- **Python 3.11** — Engine core.
- **FastAPI** — High-performance web framework for APIs.
- **Azure OpenAI client** — Direct integration for robust prompt orchestration.
- **Azure AI Search** — Cognitive search index for career knowledge base grounding.
- **ReportLab** — Dynamic PDF document generation.
- **Pandas & OpenPyXL** — Vetted career spreadsheet parsing.
- **Uvicorn** — ASGI web server.

### Frontend
- **React 18** — Component architecture.
- **Vanilla CSS** — Custom designed modern dark system with smooth visual cues.
- **Lucide React** — SVG iconography.
- **Axios** — Client-side API requests.
- **React Markdown** — Live parsing and rendering of generated action plans.

---

## 📁 Project Structure

```
careercompass-ai/
├── frontend/                  # React Frontend Application
│   ├── public/
│   ├── src/
│   │   ├── App.js             # Main App layout and state orchestration
│   │   ├── App.css            # Dark/glassmorphic custom stylesheets
│   │   ├── index.js           # React mounting point
│   │   └── index.css          # Core browser normalization styles
│   ├── package.json
│   └── .gitignore
│
├── agent.py                   # Azure OpenAI/Foundry backend agent class
├── main.py                    # FastAPI server & route handlers
├── setup_knowledge.py         # Knowledge ingestion pipeline for AI Search
├── onet_careers.xlsx          # Curated O*NET career datasets
├── onet_skills.xlsx           # Vetted O*NET skills datasets
├── requirements.txt           # Python library requirements
├── .env                       # Environment variables (ignored)
├── .gitignore                 # Git ignore config
├── README.md                  # Project documentation (this file)
└── LICENSE                    # License information
```

---

## 🧠 How It Works

1. **Profile Parsing**: The user enters a short description of their background. The backend agent uses structured system prompts to force the model to identify skills, education, and career goals in strict formats.
2. **Search Grounding**: The extracted skills query the `careers` index on Azure AI Search. Using RAG ensures the agent recommends actual recognized professions and reduces hallucinations.
3. **Multi-Criteria Optimization**: The agent evaluates transition difficulty based on O*NET parameters, ranking matches from 1 to 10.
4. **Market Validation**: When triggered, the backend reaches out to Himalayas, RemoteOK, Remotive, and Arbeitnow APIs in parallel. It normalizes queries, fetches matching job postings, and checks GitHub repository activity to return real-world indicators.
5. **Action Plan Assembly**: The roadmap and resources sections are compiled into clean Markdown content, loaded on the frontend, and formatted with custom React elements.

---

## 📊 Performance & Metrics

- **Average Inference Time**: 30-40 seconds for complete 6-step reasoning analysis.
- **Data Coverage**: Over 1,000 global occupations from O*NET and thousands of live jobs scanned on demand.
- **PDF Generation Latency**: Under 2 seconds.

---

## 🤝 Contributing

Contributions to CareerCompass AI are welcome.
1. Fork the repo.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add your feature description'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a Pull Request.

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 👤 Author

**Arya Badugu**
- SIES Graduate School of Technology, Navi Mumbai, India
- **GitHub**: [@aryabadugu](https://github.com/aryabadugu)
- **LinkedIn**: [Arya Badugu](https://linkedin.com/in/aryabadugu)