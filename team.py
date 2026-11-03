import os
import json
import re

from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient

from agents.query_agent import create_query_agent
from agents.knowledge_agent import KnowledgeBaseAgent
from agents.resolution_agent import create_resolution_agent
from agents.log_agent import LogAgent


# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================

load_dotenv()


def create_model_client():
    """Create the shared OpenAI model client."""

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Check your .env file."
        )

    return OpenAIChatCompletionClient(
        model="gpt-4o-mini",
        api_key=api_key
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def parse_agent_json(content):
    """Extract JSON returned by the Query Agent."""

    if isinstance(content, dict):
        return content

    content = content.strip()

    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    try:
        result = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError(
            "The Query Agent returned invalid JSON."
        ) from error

    if not isinstance(result, dict):
        raise ValueError(
            "The Query Agent response must be a JSON object."
        )

    required_fields = [
        "category",
        "urgency",
        "sentiment",
        "summary"
    ]

    missing_fields = [
        field for field in required_fields
        if not result.get(field)
    ]

    if missing_fields:
        raise ValueError(
            "The Query Agent response is missing: "
            + ", ".join(missing_fields)
        )

    return result


def extract_customer_complaint(customer_query):
    """
    Extract only the customer's actual complaint.

    This prevents category metadata from influencing
    the language detection performed by the Resolution Agent.
    """

    match = re.search(
        r"Customer complaint\s*:\s*(.*)",
        customer_query,
        flags=re.IGNORECASE | re.DOTALL
    )

    if match:
        return match.group(1).strip()

    return customer_query.strip()


def check_escalation(
    customer_query,
    analysis,
    knowledge_result
):
    """Determine whether human support is required."""

    urgency = str(
        analysis.get("urgency", "")
    ).strip().lower()

    sentiment = str(
        analysis.get("sentiment", "")
    ).strip().lower()

    query_lower = customer_query.lower()

    escalation_keywords = [
        "legal threat",
        "legal action",
        "lawyer",
        "attorney",
        "solicitor",
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
        "identity theft"
    ]

    reasons = []

    if urgency == "high":
        reasons.append("High urgency")

    if sentiment == "very angry":
        reasons.append("Very angry customer")

    if not knowledge_result.get("found", False):
        reasons.append(
            "No relevant knowledge-base information"
        )

    if any(
        keyword in query_lower
        for keyword in escalation_keywords
    ):
        reasons.append(
            "Legal, fraud or payment dispute concern"
        )

    if (
        "court" in query_lower
        or "sue you" in query_lower
        or "take legal action" in query_lower
    ):
        reasons.append("Potential legal threat")

    return {
        "escalated": bool(reasons),
        "reasons": list(dict.fromkeys(reasons))
    }


# ============================================================
# MAIN CUSTOMER SUPPORT WORKFLOW
# ============================================================

async def process_customer_query(
    customer_query,
    customer_details=None
):
    """
    Run the complete TechnoHexagone support workflow.

    1. Query Agent
    2. Knowledge Base Agent
    3. Escalation Check
    4. Resolution Agent
    5. Log Agent
    """

    if not isinstance(customer_query, str) or not customer_query.strip():
        raise ValueError(
            "Customer query cannot be empty."
        )

    if customer_details is None:
        customer_details = {}

    # Extract the customer's actual words separately.
    complaint_text = extract_customer_complaint(
        customer_query
    )

    model_client = create_model_client()

    try:

        # ----------------------------------------------------
        # STEP 1: CUSTOMER QUERY AGENT
        # ----------------------------------------------------

        query_agent = create_query_agent(model_client)

        query_result = await query_agent.run(
            task=customer_query
        )

        analysis = parse_agent_json(
            query_result.messages[-1].content
        )

        print("\nSTEP 1: CUSTOMER QUERY ANALYSIS")
        print(json.dumps(analysis, indent=4))

        # ----------------------------------------------------
        # STEP 2: KNOWLEDGE BASE AGENT
        # ----------------------------------------------------

        knowledge_agent = KnowledgeBaseAgent()

        knowledge_result = knowledge_agent.get_knowledge(
            customer_query
        )

        print("\nSTEP 2: KNOWLEDGE BASE RESULTS")
        print(
            "Information found:",
            knowledge_result["found"]
        )
        print(
            "Sources:",
            knowledge_result["sources"]
        )

        # ----------------------------------------------------
        # STEP 3: ESCALATION CHECK
        # ----------------------------------------------------

        escalation = check_escalation(
            customer_query,
            analysis,
            knowledge_result
        )

        print("\nSTEP 3: ESCALATION CHECK")
        print(
            "Escalated:",
            escalation["escalated"]
        )
        print(
            "Reasons:",
            escalation["reasons"]
        )

        # ----------------------------------------------------
        # STEP 4: RESOLUTION AGENT
        # ----------------------------------------------------

        resolution_agent = create_resolution_agent(
            model_client
        )

        resolution_task = f"""
IMPORTANT: RESPONSE LANGUAGE INSTRUCTION

The language of the customer's actual complaint
MUST determine the language of your response.

Read the original complaint below carefully.

- English complaint = English response.
- French complaint = French response.
- Other language = respond in that same language
  when you can do so reliably.

Do NOT use the website language to determine the response language.

Do NOT use the company location or company nationality
to determine the response language.

Do NOT use the knowledge-base document language
to determine the response language.

Do NOT use the query analysis language
to determine the response language.

Do NOT translate the customer's complaint into another language.

Write the complete customer-facing response
in the same language as the original complaint.

CUSTOMER'S ORIGINAL COMPLAINT:
{complaint_text}

CUSTOMER DETAILS:
{json.dumps(customer_details, indent=4)}

CUSTOMER QUERY ANALYSIS:
{json.dumps(analysis, indent=4)}

KNOWLEDGE BASE INFORMATION:
{knowledge_result["knowledge"]}

KNOWLEDGE SOURCES:
{", ".join(knowledge_result["sources"])}

ESCALATION INFORMATION:
Escalated: {escalation["escalated"]}
Reasons: {", ".join(escalation["reasons"])}

ADDITIONAL RESPONSE RULES:

- Generate a professional customer response.
- Use only relevant supplied knowledge-base information.
- Do not invent policies, actions or promises.
- Do not expose private customer details.
- If information is missing, ask the customer for it.
- Do not claim that an investigation or action is completed.
- If escalation is required, explain that human support
  needs to review the matter.
- Keep the response clear, polite and concise.
- Return only the customer-facing response.
"""

        resolution_result = await resolution_agent.run(
            task=resolution_task
        )

        customer_response = (
            resolution_result.messages[-1].content
        )

        print("\nSTEP 4: CUSTOMER SUPPORT RESPONSE")
        print(customer_response)

        # ----------------------------------------------------
        # STEP 5: LOG AGENT
        # ----------------------------------------------------

        log_agent = LogAgent()

        # An AI-generated response does not mean the issue
        # has actually been resolved.

        status = (
            "Escalated"
            if escalation["escalated"]
            else "Pending"
        )

        ticket_id = log_agent.log_ticket(
            customer_query=customer_query,

            category=analysis.get(
                "category", "Other"
            ),

            urgency=analysis.get(
                "urgency", "Medium"
            ),

            sentiment=analysis.get(
                "sentiment", "Neutral"
            ),

            summary=analysis.get(
                "summary", ""
            ),

            customer_response=customer_response,

            status=status,

            escalated=escalation["escalated"],

            customer_type=customer_details.get(
                "customer_type", "New"
            ),

            client_id=customer_details.get(
                "client_id", ""
            ),

            customer_name=customer_details.get(
                "customer_name", ""
            ),

            email=customer_details.get(
                "email", ""
            ),

            phone=customer_details.get(
                "phone", ""
            ),

            order_id=customer_details.get(
                "order_id", ""
            )
        )

        print("\nSTEP 5: TICKET LOGGED")
        print("Ticket ID:", ticket_id)
        print("Status:", status)

        # ----------------------------------------------------
        # RETURN COMPLETE WORKFLOW RESULTS
        # ----------------------------------------------------

        return {
            "ticket_id": ticket_id,
            "customer_details": customer_details,
            "analysis": analysis,
            "knowledge": knowledge_result,
            "response": customer_response,
            "status": status,
            "escalated": escalation["escalated"],
            "escalation_reasons": escalation["reasons"]
        }

    finally:
        await model_client.close()