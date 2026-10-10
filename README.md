# ResearchMate AI — Setup & Developer Manual

ResearchMate AI is a local-first, evidence-grounded research assistant for analyzing PDF research papers.

## Prerequisites

- **Python**: v3.10+
- **Node.js**: v18.0+
- **npm** or **yarn**

---

## Installation Commands

### 1. Backend Setup

#### Windows PowerShell:
```powershell
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
Copy-Item .env.example .env