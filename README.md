# TechnoHexagone — AI Customer Support Desk

An AI-powered customer support application built with **Python, AutoGen and Streamlit**. Four specialised agents work together to classify a customer's complaint, search company documents, prepare a grounded response, and record the support ticket.

TechnoHexagone is a fictional French electronics and technology retailer created for this project.

## Features

- **Four specialised AutoGen agents** with separate responsibilities.
- **Round-robin workflow**: Customer Query → Knowledge Base → Resolution → Log.
- **English and French support**: the response language is determined from the customer's actual complaint, independently of the website interface language.
- **Knowledge-base retrieval** from local Markdown documents, with category-aware search and source filenames.
- **Grounded responses**: the Resolution Agent is instructed not to invent company policies, prices, delivery dates, refunds, or completed actions.
- **Confidence assessment**: the Resolution Agent returns high, medium, or low confidence with a short reason.
- **Escalation rules** for high urgency, very angry sentiment, missing relevant knowledge, low resolution confidence, legal threats, fraud, and payment disputes.
- **CSV ticket logging** with customer details, complaint, classification, sources, response, confidence, status, and escalation reason.
- **Bilingual Streamlit interface** with a two-step complaint form, dashboard, latest result, ticket history, knowledge-base viewer, and response download.

## Technology stack

- Python 3.12+
- AutoGen AgentChat and AutoGen OpenAI extension
- OpenAI chat model (`gpt-4o-mini` in the current configuration)
- Streamlit
- Pandas
- python-dotenv
- Local Markdown knowledge-base documents
- CSV ticket storage

## Project structure

The submission project contains the application and its runtime files. Separate local test scripts are not required to run or demonstrate the application and are not included in this structure.

```text
customer-support-agents/
├── agents/
│   ├── __init__.py
│   ├── query_agent.py          # Complaint classification
│   ├── knowledge_agent.py      # Markdown search + AutoGen search tool
│   ├── resolution_agent.py     # Customer response + confidence
│   └── log_agent.py            # Escalation decision + CSV logging tool
├── assets/                     # Images and branding assets
├── knowledge_base/             # Company policies, FAQs and case documents
├── logs/
│   └── tickets.csv             # Created/updated by the Log Agent
├── screenshots/                # Project screenshots
├── styles/
│   └── style.css               # Streamlit styling
├── .env.example                # API-key placeholder only
├── .gitignore
├── app.py                      # Streamlit application
├── team.py                     # Four-agent AutoGen workflow
├── README.md
└── requirements.txt
```

The knowledge base currently contains **37 Markdown documents**.

## Setup on Windows

### 1. Open the project folder

Open the project in Visual Studio Code. In the VS Code terminal, move to the project directory:

```powershell
cd D:\customer-support-agents
```

### 2. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use the execution-policy instructions appropriate for your Windows environment, or activate the environment from the VS Code Python interpreter selector.

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure the OpenAI API key

Create a file named `.env` in the project root, next to `app.py`, containing:

```text
OPENAI_API_KEY=your_openai_api_key_here
```

Use your own API key. Do not paste it into source code, screenshots, README files, or public repositories. Confirm that `.env` is listed in `.gitignore` before publishing the project.

The `.env.example` file should contain only a placeholder:

```text
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. Run the application

From the project root, with the virtual environment activated:

```powershell
streamlit run app.py
```

Streamlit displays a local URL in the terminal, usually `http://localhost:8501`.

## How the four-agent workflow works

The application passes the initial customer request and customer details to `process_customer_query()` in `team.py`. The workflow extracts the customer's actual complaint and detects whether it is in English or French. The detected language is then included as an explicit instruction for the Resolution Agent.

1. **Customer Query Agent** — classifies the complaint and returns its category, urgency, sentiment, and summary.
2. **Knowledge Base Agent** — calls its Python search tool to retrieve relevant passages from local Markdown documents. The search uses the complaint category and returns source filenames.
3. **Resolution Agent** — uses the complaint, classification, and retrieved knowledge to prepare the customer-facing response. It also returns a confidence level and reason. Its output is normal JSON text so it can be relayed by the current AutoGen group-chat runtime.
4. **Log Agent** — calls its Python logging tool. The tool applies the escalation rules, determines the ticket status, and appends the ticket to `logs/tickets.csv`.

The agents run in a `RoundRobinGroupChat` in the order shown above. The team stops when the Log Agent returns the `LOGGED` marker, with a maximum-message termination condition as a safety limit.

## Escalation rules

A ticket is marked **Escalated** when one or more of these conditions apply:

- The Query Agent classifies urgency as **High**.
- Customer sentiment is **Very Angry**.
- No sufficiently relevant knowledge-base information is found.
- Resolution confidence is **Low**.
- The complaint contains a detected legal threat, fraud concern, or payment dispute.

When none of these conditions applies, the current workflow records the ticket as **Resolved**. This is the workflow's ticket status; it does not mean that the application has accessed an order system or performed a refund, cancellation, replacement, or other real-world action. The customer response must not claim that such an action has been completed unless the supplied information confirms it.

## Ticket log

Tickets are appended to `logs/tickets.csv`. The logger creates the `logs` directory and CSV file when needed. It preserves existing records when required columns are added.

The log includes fields for:

- Ticket ID and date/time
- Customer type, client ID, name, email, phone, and order ID
- Original customer query
- Category, urgency, sentiment, and summary
- Knowledge-base source filenames
- Customer-facing response
- Resolution confidence and confidence reason
- Status, escalation flag, and escalation reason

Close the CSV file in Excel or another spreadsheet program before submitting a new request if Windows reports that the file is locked.

## Demonstration and manual testing

The application is demonstrated and checked directly through the Streamlit interface. No separate `test_*.py` scripts are needed to launch or demonstrate the project.

1. Start the app with `streamlit run app.py`.
2. Open **New Complaint** and complete the customer details form.
3. Select a complaint category and enter a complaint in English or French.
4. Submit the complaint and review the original customer request, AI response, classification, knowledge-base sources, confidence, and escalation status on the Latest Result page.
5. Open **Ticket History** to confirm that the ticket was saved and to view or download the CSV log.

Suggested demo scenarios:

| Scenario | What it demonstrates |
|---|---|
| English: order has not arrived | Shipping classification, shipping-policy retrieval, English response |
| English: forgotten password | Account classification and account guidance |
| English: return request | Returns classification and relevant return-policy information |
| English: duplicate card charge with legal threat | Billing classification and human-support escalation |
| French: damaged or faulty product | French complaint detection and French customer response |
| French: unsupported gift-card request | No matching document, honest response, and escalation |

The Query Agent's sentiment and urgency are model classifications. Their actual outputs should be reviewed during the demonstration rather than assumed in advance.

For submission screenshots, capture at least one non-escalated ticket, one escalated ticket, and the Ticket History table. Use fictional customer details and check screenshots for API keys or personal information before sharing them.

## Streamlit interface

The website includes:

- English/French interface selector
- Two-step customer details and complaint form
- Overview dashboard and ticket metrics
- Latest Result page showing the customer's original request above the AI response
- Ticket ID, category, urgency, and status
- Escalation status and reasons
- Expandable AI analysis and knowledge-base sources
- Customer response download
- Ticket History table and CSV download
- Knowledge Base document viewer
- About page

The website language changes interface labels. The customer-facing response language is determined separately from the customer's complaint.

## Security and project hygiene

- Keep `.env` out of Git and public uploads.
- Commit `.env.example` only with a placeholder, never a working key.
- Do not include real customer personal information in screenshots or shared demonstration data.
- Do not publish ticket logs containing customer names, emails, phone numbers, or client IDs.
- Local development test scripts can remain on the developer's computer; they are not needed in the submitted project.
