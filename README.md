# TechnoHexagone — AI Customer Support Desk

An AI-powered customer support demonstration for TechnoHexagone, a fictional French electronics retailer. The application uses four specialised agents to analyse customer complaints, retrieve relevant company information, draft a customer-facing response, and record each ticket.

The user interface is available in English and French. The response language is determined by the language used in the customer's complaint, independently of the selected website language.

## Features

- Four specialised agents: Customer Query, Knowledge Base, Resolution, and Log.
- Complaint analysis: identifies the category, urgency, sentiment, and a short summary.
- Knowledge retrieval: searches the company's Markdown knowledge-base documents and returns relevant information and source filenames.
- Customer-facing replies: drafts a polite response based on retrieved company information.
- Escalation: flags high-urgency, very angry, no-match, legal, fraud, and payment-dispute cases for human support.
- Ticket logging: records each submitted complaint and its response in 'logs/tickets.csv'.
- Bilingual website: switch the interface between English and French.
- Language-aware responses: English complaints receive English replies; French complaints receive French replies.
- Phone-number validation: accepts common phone-number formatting and rejects letters. The phone field is optional.
- Streamlit dashboard: displays ticket metrics, recent activity, and ticket-category distribution.
- Ticket history: search, view, and download ticket records.

Important: This is a demonstration application. It does not connect to a live order-management, payment, shipping, or customer-account system. It cannot actually issue refunds, change orders, or verify customer IDs. The AI response must not be treated as confirmation that an action has been completed.

## Technology

- Python 3.10+
- AutoGen ('autogen-agentchat' and 'autogen-ext[openai]')
- OpenAI chat model client ('gpt-4o-mini' in the current configuration)
- Streamlit
- Pandas
- python-dotenv
- Markdown files for the knowledge base
- CSV for ticket logging

## Project structure

customer-support-agents/
│
├── agents/
│   ├── __init__.py
│   ├── query_agent.py
│   ├── knowledge_agent.py
│   ├── resolution_agent.py
│   └── log_agent.py
│
├── assets/
│   ├── background_hexagons.png
│   ├── background_wave.png
│   ├── electronics_banner.png
│   ├── logo_compact.png
│   ├── logo_wordmark.png
│   ├── product_illustration.png
│   ├── support_agent_illustration.png
│   └── support_banner.png
│
├── knowledge_base/
│   └── Markdown company policy, FAQ, product, and support documents
│
├── logs/
│   └── tickets.csv
│
├── Outputs/
│   └── Application sample tested screenshots 
│
├── styles/
│   └── style.css
│
├── app.py
├── team.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md