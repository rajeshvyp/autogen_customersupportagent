import csv
import re
import unicodedata

from pathlib import Path
from datetime import datetime

from autogen_agentchat.agents import AssistantAgent


# ============================================================
# LOGGING CLASS
# ============================================================

class LogAgent:
    def __init__(self, log_file="logs/tickets.csv"):
        self.log_file = Path(log_file)

        self.log_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.headers = []
        self.create_log_file()

    def create_log_file(self):
        """Create the CSV file and preserve existing records."""

        required_headers = [
            "Ticket_ID",
            "Date_Time",
            "Customer_Type",
            "Client_ID",
            "Customer_Name",
            "Email",
            "Phone",
            "Order_ID",
            "Customer_Query",
            "Category",
            "Urgency",
            "Sentiment",
            "Summary",
            "Knowledge_Sources",
            "Customer_Response",
            "Resolution_Confidence",
            "Confidence_Reason",
            "Status",
            "Escalated",
            "Escalation_Reason"
        ]

        if not self.log_file.exists():

            self.headers = required_headers

            with open(
                self.log_file,
                mode="w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)
                writer.writerow(self.headers)

            return

        # Read the existing CSV headers and rows.
        with open(
            self.log_file,
            mode="r",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            reader = csv.DictReader(file)
            old_headers = reader.fieldnames or []
            rows = list(reader)

        if not old_headers:
            self.headers = required_headers
        else:
            # Keep existing columns and append missing columns.
            missing_headers = [
                header
                for header in required_headers
                if header not in old_headers
            ]

            self.headers = old_headers + missing_headers

        # Rewrite the file only when its structure needs updating.
        if self.headers != old_headers:

            with open(
                self.log_file,
                mode="w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.DictWriter(
                    file,
                    fieldnames=self.headers,
                    extrasaction="ignore"
                )

                writer.writeheader()
                writer.writerows(rows)

    def log_ticket(
        self,
        customer_query,
        category,
        urgency,
        sentiment,
        summary,
        customer_response,
        status="Resolved",
        escalated=False,
        customer_type="New",
        client_id="",
        customer_name="",
        email="",
        phone="",
        order_id="",
        knowledge_sources="",
        resolution_confidence="",
        confidence_reason="",
        escalation_reason=""
    ):
        """Record the customer support interaction in the CSV."""

        now = datetime.now()

        ticket_id = (
            "TH-" +
            now.strftime("%Y%m%d%H%M%S%f")
        )

        ticket = {
            "Ticket_ID": ticket_id,
            "Date_Time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "Customer_Type": customer_type,
            "Client_ID": client_id,
            "Customer_Name": customer_name,
            "Email": email,
            "Phone": phone,
            "Order_ID": order_id,
            "Customer_Query": customer_query,
            "Category": category,
            "Urgency": urgency,
            "Sentiment": sentiment,
            "Summary": summary,
            "Knowledge_Sources": knowledge_sources,
            "Customer_Response": customer_response,
            "Resolution_Confidence": resolution_confidence,
            "Confidence_Reason": confidence_reason,
            "Status": status,
            "Escalated": escalated,
            "Escalation_Reason": escalation_reason
        }

        with open(
            self.log_file,
            mode="a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=self.headers,
                extrasaction="ignore"
            )

            writer.writerow(ticket)

        print(
            f"Ticket {ticket_id} successfully logged."
        )

        return ticket_id


# ============================================================
# ESCALATION HELPER
# ============================================================

def normalize_text(text):
    """Normalize accents and case for keyword matching."""

    text = str(text or "").lower()

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    return "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )


def determine_escalation(
    complaint_text,
    urgency,
    sentiment,
    knowledge_found,
    resolution_confidence
):
    """Apply the assignment's escalation rules."""

    complaint = normalize_text(complaint_text)

    urgency = str(urgency or "").strip().lower()
    sentiment = str(sentiment or "").strip().lower()
    confidence = str(
        resolution_confidence or ""
    ).strip().lower()

    reasons = []

    if urgency == "high":
        reasons.append("High urgency")

    if sentiment == "very angry":
        reasons.append("Very angry customer")

    if not knowledge_found:
        reasons.append(
            "No relevant knowledge-base information"
        )

    if confidence == "low":
        reasons.append(
            "Low resolution confidence"
        )

    escalation_keywords = [
        # Legal concerns
        "legal threat",
        "legal action",
        "lawyer",
        "attorney",
        "solicitor",
        "court",
        "sue you",
        "take legal action",
        "menace juridique",
        "action en justice",
        "avocat",
        "tribunal",
        "porter plainte",
        "poursuites judiciaires",

        # Fraud and payment disputes
        "fraud",
        "fraudulent",
        "unauthorized payment",
        "unauthorised payment",
        "unauthorized transaction",
        "unauthorised transaction",
        "duplicate charge",
        "charged twice",
        "payment dispute",
        "chargeback",
        "stolen card",
        "identity theft",
        "fraude",
        "paiement non autorise",
        "prelevement non autorise",
        "facture deux fois",
        "debite deux fois",
        "double debit",
        "contester le paiement",
        "carte volee"
    ]

    if any(
        keyword in complaint
        for keyword in escalation_keywords
    ):
        reasons.append(
            "Legal, fraud or payment dispute concern"
        )

    reasons = list(dict.fromkeys(reasons))

    return {
        "escalated": bool(reasons),
        "reasons": reasons
    }


# ============================================================
# AUTOGEN LOG AGENT
# ============================================================

def create_log_agent(
    model_client,
    log_file="logs/tickets.csv"
):
    """
    Creates the AutoGen Log Agent.

    The agent uses a Python tool to determine escalation
    and save each support ticket.
    """

    logger = LogAgent(log_file=log_file)

    def save_support_ticket(
        customer_query: str,
        complaint_text: str,
        category: str,
        urgency: str,
        sentiment: str,
        summary: str,
        knowledge_found: bool,
        knowledge_sources: str,
        customer_response: str,
        resolution_confidence: str,
        confidence_reason: str,
        customer_type: str,
        client_id: str,
        customer_name: str,
        email: str,
        phone: str,
        order_id: str
    ) -> str:
        """
        Determine escalation and save the support ticket.

        The escalation decision is calculated by Python,
        rather than left to an unsupported model assumption.
        """

        escalation = determine_escalation(
            complaint_text=complaint_text,
            urgency=urgency,
            sentiment=sentiment,
            knowledge_found=knowledge_found,
            resolution_confidence=resolution_confidence
        )

        status = (
            "Escalated"
            if escalation["escalated"]
            else "Resolved"
        )

        escalation_reason = "; ".join(
            escalation["reasons"]
        )

        try:

            ticket_id = logger.log_ticket(
                customer_query=customer_query,
                category=category,
                urgency=urgency,
                sentiment=sentiment,
                summary=summary,
                customer_response=customer_response,
                status=status,
                escalated=escalation["escalated"],
                customer_type=customer_type,
                client_id=client_id,
                customer_name=customer_name,
                email=email,
                phone=phone,
                order_id=order_id,
                knowledge_sources=knowledge_sources,
                resolution_confidence=resolution_confidence,
                confidence_reason=confidence_reason,
                escalation_reason=escalation_reason
            )

            return (
                f"LOGGED: Ticket successfully saved. "
                f"Ticket ID: {ticket_id}. "
                f"Status: {status}. "
                f"Escalated: {escalation['escalated']}. "
                f"Escalation reasons: "
                f"{escalation_reason or 'None'}"
            )

        except PermissionError:
            return (
                "LOGGING_FAILED: The ticket could not be saved. "
                "Check whether tickets.csv is open in another program."
            )

    log_agent = AssistantAgent(
        name="log_agent",

        description=(
            "Determines escalation status and records completed "
            "customer support tickets in the CSV log."
        ),

        model_client=model_client,

        tools=[
            save_support_ticket
        ],

        max_tool_iterations=1,

        reflect_on_tool_use=False,

        system_message="""
You are the Log Agent for TechnoHexagone.

YOUR RESPONSIBILITY:

Record the completed customer support interaction
and apply the assignment's escalation rules.

INFORMATION TO COLLECT:

Use the original task and all previous agent messages:

1. Original customer query.
2. Actual customer complaint text.
3. Query Agent category.
4. Query Agent urgency.
5. Query Agent sentiment.
6. Query Agent summary.
7. Knowledge Agent found/not-found result.
8. Knowledge Agent source filenames.
9. Resolution Agent customer-facing response.
10. Resolution Agent confidence.
11. Resolution Agent confidence reason.
12. Customer type.
13. Client ID.
14. Customer name.
15. Email.
16. Phone.
17. Order ID.

IMPORTANT:

Use the Resolution Agent's structured output fields:
- response
- confidence
- confidence_reason

Do not confuse the confidence reason with the escalation reason.

TOOL REQUIREMENT:

You MUST call save_support_ticket exactly once.

Pass all 17 required arguments.

Use the original complaint text for complaint_text.
Use the complete initial customer query for customer_query.

For unavailable optional customer details, use empty strings.

For knowledge_sources, pass the source filenames as a
semicolon-separated string.

For knowledge_found, pass a boolean value.

ESCALATION:

The Python tool determines whether escalation is required.

It checks:
- High urgency.
- Very angry customer.
- No relevant knowledge-base information.
- Low resolution confidence.
- Legal threats.
- Fraud.
- Payment disputes.

Do not invent or override the tool's escalation decision.

OUTPUT:

After calling the tool, return its result.

Do not claim the ticket was logged unless the tool
confirms successful logging.

Do not generate a customer-facing response.
Do not expose unnecessary customer information.
"""
    )

    return log_agent