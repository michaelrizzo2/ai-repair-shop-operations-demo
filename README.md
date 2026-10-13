# AI Repair Shop Operations Demo

An interactive portfolio project by Michael Rizzo, based on computer repair shop workflows and built exclusively with fictional business data.

**Status: project initialized. Application code, evaluations, and hosted demo are not yet available.**

[Portfolio](https://michaelrizzo2.github.io/#projects) · [Repository](https://github.com/michaelrizzo2/ai-repair-shop-operations-demo)

## What the demo will do

A visitor selects a fictional repair request and watches the workflow run:

1. Extract the device, symptoms, and missing information into a validated schema.
2. Query sandbox inventory and appointment tools.
3. Calculate a provisional estimate using deterministic Python rules.
4. Draft a customer response grounded in tool results.
5. Require human approval before a simulated booking.

Example: “My laptop won’t charge. Can you give me a price and book a repair?” The system should request the device model before choosing a compatible part; a symptom alone is not a confirmed diagnosis.

The interface will show concise workflow events, tool inputs and outputs, estimate line items, latency, and errors. It will not expose private model reasoning.

## Planned architecture

Browser UI → Python/FastAPI backend → structured AI extraction and response drafting → allowlisted sandbox tools. Python owns pricing, validation, permissions, and approval gates.

Serve the HTML/CSS/JavaScript frontend from the same FastAPI application to simplify deployment. Stream workflow events with server-sent events (SSE). Start with one orchestrated workflow; add agents only when a specific task benefits from them.

## Public demo data and boundaries

- Use invented devices, inventory, prices, customers, and appointment slots; label all records as synthetic.
- Never connect this public deployment to production email, customer records, billing, or calendars.
- Keep AI credentials on the server in environment variables. Never put them in JavaScript, Git, screenshots, or logs.
- Use isolated, expiring sessions. Bind simulated approval to the current session and proposed action.
- Start with preset requests. If free-text input is added, tell visitors not to enter personal information and avoid retaining it.
- Restrict tools to sandbox operations; validate model output and tool arguments.
- Add request limits, input limits, model timeouts, output limits, and a usage budget before public launch.
- Approval creates a fictional sandbox booking only; no real email is sent and no payment is taken.

## Get the repository onto your computer

Install Git and Python 3.11 or newer, then run:

```bash
git clone https://github.com/michaelrizzo2/ai-repair-shop-operations-demo.git
cd ai-repair-shop-operations-demo
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, use `py -m venv .venv` and `.venv\Scripts\Activate.ps1` instead.

Before adding credentials, create `.gitignore` containing:

```gitignore
.env
.env.*
!.env.example
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
*.log
*.sqlite
*.sqlite3
```

## Code to add next

The following is the proposed structure, not files currently included in this repository:

```text
app/
  __init__.py
  main.py             # FastAPI app, frontend serving, health endpoint
  schemas.py          # Validated request, estimate, and action schemas
  workflow.py         # Intake → tools → estimate → draft → approval
  tools.py            # Synthetic inventory and appointment tools
  pricing.py          # Deterministic estimate calculations
  static/
    index.html
    app.js
    styles.css
data/
  inventory.json      # Invented records only
  appointments.json
evals/
  cases.json          # Representative cases and expected outcomes
tests/
requirements.txt
.env.example          # Variable names and placeholders only
.gitignore
README.md
```

First milestone: implement one complete charging-problem workflow with fictional inventory, an itemized estimate, and a simulated approval action. Begin with a deterministic mode that runs without credentials; label it clearly. Add a real model adapter afterward and identify the active mode in the UI.

Once `requirements.txt` and `app/main.py` exist:

```bash
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`. These commands will not run until the application files have been added. Keep optional model credentials in your local `.env` and ensure the application explicitly loads them; publish only placeholders in `.env.example`.

## Push your code to GitHub

From the cloned repository:

```bash
git status
git add .gitignore .env.example requirements.txt app data evals tests README.md
git diff --cached
git commit -m "Build repair intake and estimate demo"
git push origin main
```

Stage only paths that actually exist. Review the staged diff for credentials or real business data before committing. GitHub may ask you to authenticate with your configured Git credential manager or SSH setup.

## Make the demo live and interactive

The existing GitHub Pages portfolio can link to the application. Deploy the Python backend and its frontend as a web service; GitHub Pages does not run a Python server.

After the code works locally:

1. In Render, create a Web Service connected to this GitHub repository and the `main` branch.
2. Choose Python as the runtime.
3. Set build command: `pip install -r requirements.txt`.
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
5. Add required environment variables in the hosting dashboard, never in committed files. Start in deterministic demo mode, then enable the model adapter after configuring usage limits.
6. Deploy and test the hosted URL on desktop and mobile. Verify SSE events appear incrementally, sessions remain isolated, and failures display clearly.
7. Add the verified URL here as **Live Demo**, and add both **Live Demo** and **Source Code** links to the portfolio project card.

Select a hosting plan based on current pricing and whether cold starts are acceptable. Persistent demo records are unnecessary if each session uses temporary synthetic state.

References: [Render FastAPI deployment](https://render.com/docs/deploy-fastapi), [GitHub Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages).

## Evidence to publish before calling it complete

- Tests for estimate arithmetic, part compatibility, approval requirements, and session isolation.
- Evaluation cases for missing model details, unavailable parts, unsupported requests, tool failures, and attempts to bypass approval.
- Measured extraction accuracy, correct clarification/escalation rates, latency, and approximate model cost per run, with sample size and model configuration.
- A short demo recording and architecture diagram.
- Clear distinction between deterministic demo behavior and actual model behavior.

## Immediate next step

Clone the repository, add `.gitignore`, and build the first synthetic repair request → estimate → approval workflow.
