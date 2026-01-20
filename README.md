# RepoBlueprint AI v3.0

**Architectural Intelligence Engine** — Instant, evidence-based, executable architecture understanding.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-green.svg)

RepoBlueprint AI transforms any repository into a comprehensive architectural model. It combines AST-based parsing (Tree-sitter) with local LLMs (Ollama) to generate interactive diagrams, architectural insights, and diffs between commits.

## 🌟 What's New in v3.0: Premium UI/UX

-   **💎 Billion-Dollar Aesthetic**: A complete redesign following modern SaaS standards (Linear, Vercel, Stripe style).
-   **🎨 Comprehensive Design System**: Unified typography, spacing, and color palettes for a consistent, professional look.
-   **✨ Glassmorphism & Animations**: Smooth interactions, glass-card layouts, and refined micro-animations using Framer Motion.
-   **📱 Robust Responsiveness**: Grid-based layouts ensure perfect rendering on all device sizes without content overlap or "packing".

## 🚀 Key Features

-   **🧠 Architectural Knowledge Graph (AKG)**: Maps components, dependencies, and layers with evidence anchoring.
-   **🔍 Natural Language Query**: Ask questions like "Where is the authentication logic?" or "What depends on the User service?".
-   **🔄 Blueprint Diff**: Compare architecture between branches or commits to detect breaking changes and drift.
-   **📊 Interactive Diagrams**: Auto-generated C4 Context, Container, and Component diagrams (Mermaid.js).
-   **📑 Multi-Format Export**: specialized reports in Markdown, HTML (standalone), and JSON.
-   **🔐 100% Local Privacy**: Runs entirely on your machine using Ollama. Zero code leaves your environment.

## 🛠️ Tech Stack

-   **Backend**: Python 3.11, FastAPI, NetworkX, GitPython, Tree-sitter
-   **Frontend**: Next.js 15, TypeScript, Tailwind CSS, Shadcn/UI, Framer Motion
-   **AI/ML**: Ollama (Qwen2.5-Coder / Llama 3), LangChain
-   **Infrastructure**: Docker, Docker Compose

## 🏁 Quick Start

### Prerequisites

-   [Docker & Docker Compose](https://www.docker.com/products/docker-desktop/)
-   [Ollama](https://ollama.com/) running locally (default: `http://localhost:11434`)

### Run with Docker

```bash
# 1. Clone the repository
git clone https://github.com/harleysederholm-alt/BluePrint.git
cd BluePrint

# 2. Start the application
docker-compose up --build
```

Access the application:
-   **Frontend**: [http://localhost:3000](http://localhost:3000)
-   **Backend API**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Manual Setup (Development)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📖 Usage Guides

### Analyzing a Repository
1.  Enter a GitHub/GitLab URL on the home page.
2.  Select an audience profile (Engineer, Manager, Architect).
3.  Watch the real-time analysis as agents parse code and build the graph.

### Querying the Graph
Use the **Query** tab to ask questions:
-   *"Find all controllers in the payment module"*
-   *"Show me circular dependencies"*
-   *"Analyze the complexity of the DataLayer"*

### Exporting Reports
Click the **Export** button to download:
-   `Analysis.md` - Comprehensive architecture report.
-   `Analysis.html` - Self-contained offline report with interactive diagrams.

## 🧪 Testing

```bash
# Backend tests
cd backend && pytest

# Frontend type check
cd frontend && npx tsc --noEmit
```

## 📄 License

MIT © 2026 RepoBlueprint AI
