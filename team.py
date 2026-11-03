
import os
import json
import re
import unicodedata

from dotenv import load_dotenv

from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import (
    TextMentionTermination,
    MaxMessageTermination
)

from agents.query_agent import create_query_agent
from agents.knowledge_agent import create_knowledge_agent
from agents.resolution_agent import create_resolution_agent
from agents.log_agent import (
    create_log_agent,
    determine_escalation
)


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
# LANGUAGE DETECTION
# ============================================================

def extract_customer_complaint(customer_query):
    """
    Extract only the customer's actual complaint.

    This excludes website metadata such as the selected category.
    """

    match = re.search(
        r"Customer complaint\s*:\s*(.*)",
        customer_query,
        flags=re.IGNORECASE | re.DOTALL
    )

    if match:
        return match.group(1).strip()

    return customer_query.strip()


def detect_complaint_language(complaint_text):
    """
    Detect English or French using the customer's actual words.

    This does not use the website language, company location,
    or knowledge-base document language.
    """

    original_text = str(complaint_text or "").strip().lower()

    if not original_text:
        return "English"

    normalized_text = unicodedata.normalize(
        "NFKD",
        original_text
    )

    normalized_text = "".join(
        character
        for character in normalized_text
        if not unicodedata.combining(character)
    )

    words = re.findall(
        r"[a-z]+",
        normalized_text
    )

    english_words = {
        "i", "my", "mine", "we", "our", "ours",
        "the", "an", "and", "but", "or",
        "is", "are", "was", "were", "am",
        "have", "has", "had", "do", "does", "did",
        "not", "to", "for", "of", "in", "on",
        "with", "from", "this", "that", "these",
        "it", "they", "them", "you", "your",
        "because", "what", "where", "when", "how",
        "who", "why", "could", "would", "should",
        "will", "there", "their", "about", "after",
        "before", "still", "ordered", "arrived",
        "delivery", "refund", "charged", "twice",
        "please", "nobody", "updated", "extremely",
        "frustrated", "cannot", "received", "delayed",
        "broken", "product", "account", "password",
        "help", "need", "want", "order", "late"
    }

    french_words = {
        "je", "nous", "mon", "ma", "mes",
        "notre", "nos", "votre", "vos",
        "le", "la", "les", "un", "une",
        "des", "du", "et", "mais",
        "est", "sont", "suis", "etes",
        "ai", "avons", "avez", "ont",
        "pas", "plus", "pour", "dans",
        "avec", "sans", "sur", "ce", "cette",
        "ces", "il", "elle", "ils", "elles",
        "que", "qui", "quoi", "comment",
        "pourquoi", "quand", "commande",
        "livraison", "remboursement", "facture",
        "recu", "depuis", "toujours", "encore",
        "parce", "etre", "avoir", "faire",
        "peux", "pouvez", "merci", "bonjour",
        "retard", "colis", "arrive", "arrivee",
        "deux", "semaines", "jours", "hier",
        "souhaite", "voudrais", "demande",
        "probleme", "produit", "compte",
        "mot", "passe", "aide", "besoin",
        "acheter", "commande", "annule"
    }

    english_score = sum(
        1 for word in words
        if word in english_words
    )

    french_score = sum(
        1 for word in words
        if word in french_words
    )

    # Additional French sentence-pattern signals.
    french_patterns = [
        r"\bj['’]ai\b",
        r"\bj['’]aimerais\b",
        r"\bje suis\b",
        r"\bje voudrais\b",
        r"\bje veux\b",
        r"\bil y a\b",
        r"\bn['’]est pas\b",
        r"\bne\b.*\bpas\b",
        r"\bma commande\b",
        r"\bmon colis\b"
    ]

    for pattern in french_patterns:
        if re.search(pattern, normalized_text):
            french_score += 2

    # Additional English sentence-pattern signals.
    english_patterns = [
        r"\bi am\b",
        r"\bi have\b",
        r"\bi need\b",
        r"\bi want\b",
        r"\bi ordered\b",
        r"\bwhere is\b",
        r"\bhas not\b",
        r"\bhasn't\b",
        r"\bit is\b",
        r"\bi cannot\b",
        r"\bi can't\b"
    ]

    for pattern in english_patterns:
        if re.search(pattern, original_text):
            english_score += 2

    # Accented characters are an additional French signal.
    french_accents = "àâçéèêëîïôùûüÿœ"

    if any(
        character in original_text
        for character in french_accents
    ):
        french_score += 2

    # English is the fallback when the language is unclear.
    if french_score > english_score:
        return "French"

    return "English"


# ============================================================
# MESSAGE AND JSON HELPERS
# ============================================================

def get_agent_content(messages, agent_name):
    """Retrieve the latest message from a specific agent."""

    for message in reversed(messages):

        if getattr(message, "source", None) == agent_name:
            return getattr(message, "content", None)

    raise RuntimeError(
        f"No output was received from {agent_name}."
    )


def parse_json_content(content, agent_name):
    """Convert an agent's JSON output into a Python dictionary."""

    if hasattr(content, "model_dump"):
        content = content.model_dump()

    if isinstance(content, dict):
        return content

    if isinstance(content, str):
        text = content.strip()
    else:
        text = str(content).strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    try:
        result = json.loads(text)

    except json.JSONDecodeError:

        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or end <= start:
            raise ValueError(
                f"{agent_name} did not return valid JSON."
            )

        try:
            result = json.loads(
                text[start:end + 1]
            )

        except json.JSONDecodeError as error:
            raise ValueError(
                f"{agent_name} returned invalid JSON."
            ) from error

    if not isinstance(result, dict):
        raise ValueError(
            f"{agent_name} output must be a JSON object."
        )

    return result


def parse_agent_json(content):
    """Validate the Customer Query Agent's result."""

    result = parse_json_content(
        content,
        "Customer Query Agent"
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


def parse_knowledge_result(content):
    """Validate and normalize the Knowledge Agent's result."""

    result = parse_json_content(
        content,
        "Knowledge Base Agent"
    )

    found = result.get("found", False)

    if isinstance(found, str):
        found = found.strip().lower() in (
            "true", "yes", "1"
        )

    result["found"] = bool(found)

    sources = result.get("sources", [])

    if isinstance(sources, str):
        sources = [sources] if sources.strip() else []

    result["sources"] = sources or []

    knowledge = result.get("knowledge", "")

    if knowledge is None:
        knowledge = ""

    result["knowledge"] = str(knowledge)

    return result


def parse_resolution_result(content):
    """Extract the Resolution Agent's JSON result."""

    result = parse_json_content(
        content,
        "Resolution Agent"
    )

    response = result.get("response")

    confidence = str(
        result.get("confidence", "")
    ).strip().lower()

    confidence_reason = str(
        result.get("confidence_reason", "")
    ).strip()

    if not isinstance(response, str) or not response.strip():
        raise ValueError(
            "The Resolution Agent did not return a customer response."
        )

    if confidence not in ("high", "medium", "low"):
        raise ValueError(
            "The Resolution Agent returned an invalid confidence level."
        )

    if not confidence_reason:
        raise ValueError(
            "The Resolution Agent did not provide a confidence reason."
        )

    return {
        "response": response.strip(),
        "confidence": confidence,
        "confidence_reason": confidence_reason
    }


def extract_ticket_id(log_output):
    """Extract the ticket ID from the Log Agent confirmation."""

    match = re.search(
        r"Ticket ID:\s*(TH-[A-Za-z0-9-]+)",
        log_output,
        flags=re.IGNORECASE
    )

    if not match:
        raise RuntimeError(
            "The Log Agent did not provide a valid ticket ID."
        )

    return match.group(1)


# ============================================================
# MAIN CUSTOMER SUPPORT WORKFLOW
# ============================================================

async def process_customer_query(
    customer_query,
    customer_details=None
):
    """
    Run the complete four-agent TechnoHexagone workflow.

    1. Customer Query Agent
    2. Knowledge Base Agent
    3. Resolution Agent
    4. Log Agent

    The response language is determined from the original
    customer complaint, independently of website language.
    """

    if (
        not isinstance(customer_query, str)
        or not customer_query.strip()
    ):
        raise ValueError(
            "Customer query cannot be empty."
        )

    if customer_details is None:
        customer_details = {}

    if not isinstance(customer_details, dict):
        raise ValueError(
            "Customer details must be provided as a dictionary."
        )

    # --------------------------------------------------------
    # EXTRACT AND DETECT THE ACTUAL COMPLAINT LANGUAGE
    # --------------------------------------------------------

    complaint_text = extract_customer_complaint(
        customer_query
    )

    complaint_language = detect_complaint_language(
        complaint_text
    )

    print(
        "\nDetected complaint language:",
        complaint_language
    )

    model_client = create_model_client()

    try:

        # ----------------------------------------------------
        # STEP 1: CREATE THE FOUR AUTOGEN AGENTS
        # ----------------------------------------------------

        query_agent = create_query_agent(model_client)

        knowledge_agent = create_knowledge_agent(
            model_client
        )

        resolution_agent = create_resolution_agent(
            model_client
        )

        log_agent = create_log_agent(
            model_client
        )

        # ----------------------------------------------------
        # STEP 2: DEFINE TERMINATION CONDITIONS
        # ----------------------------------------------------

        termination = (
            TextMentionTermination(
                "LOGGED",
                sources=["log_agent"]
            )
            | MaxMessageTermination(
                max_messages=5
            )
        )

        # ----------------------------------------------------
        # STEP 3: CREATE THE ROUND-ROBIN TEAM
        # ----------------------------------------------------

        support_team = RoundRobinGroupChat(
            participants=[
                query_agent,
                knowledge_agent,
                resolution_agent,
                log_agent
            ],
            termination_condition=termination
        )

        # ----------------------------------------------------
        # STEP 4: PREPARE THE INITIAL CUSTOMER TASK
        # ----------------------------------------------------

        initial_task = f"""
TECHNOHEXAGONE CUSTOMER SUPPORT WORKFLOW

CUSTOMER DETAILS:
{json.dumps(customer_details, indent=4, ensure_ascii=False)}

ORIGINAL CUSTOMER QUERY:
{customer_query}

CUSTOMER'S ACTUAL COMPLAINT:
{complaint_text}

============================================================
MANDATORY CUSTOMER RESPONSE LANGUAGE
============================================================

{complaint_language}

The application has determined this language directly
from the customer's actual complaint.

The Resolution Agent MUST write the entire customer-facing
response in {complaint_language}.

This instruction is authoritative.

Do NOT use the website interface language to choose
the customer response language.

Do NOT use the company location or nationality.

Do NOT use the knowledge-base document language.

Do NOT use the language of previous agents' messages.

The actual complaint language is the only language
that determines the customer-facing response.

============================================================
AGENT WORKFLOW
============================================================

The agents must work in this exact order:

1. CUSTOMER QUERY AGENT

Analyse the original customer query.

Return:
- category
- urgency
- sentiment
- summary

Return a JSON object.

2. KNOWLEDGE BASE AGENT

Use the Query Agent's summary and category to search
the company's knowledge-base documents.

You MUST use your Python search tool.

Return:
- found (true or false)
- sources (list of source filenames)
- knowledge (relevant retrieved information)

Preserve the source filenames.

3. RESOLUTION AGENT

Use:
- Original customer complaint.
- Mandatory customer response language above.
- Query Agent classification.
- Knowledge Base Agent results.

Write a professional customer-facing response.

Assess confidence as HIGH, MEDIUM or LOW.

The response language MUST be {complaint_language}.

The escalation conditions are:

- High urgency.
- Very angry customer.
- No relevant knowledge-base information.
- Legal threats.
- Fraud or payment disputes.
- Low resolution confidence.

When any condition applies, explain appropriately that
human support needs to review the matter.

Return the required JSON fields:
- response
- confidence
- confidence_reason

4. LOG AGENT

Use the information from all previous agents and the
customer details in this initial task.

You MUST call your save_support_ticket Python tool
exactly once.

The tool determines the final escalation status and
writes the ticket to the CSV file.

Do not claim successful logging before the tool confirms it.

The team must stop after the Log Agent successfully
returns the marker LOGGED.

GENERAL RULES:

- Do not invent company policies or customer information.
- Do not change the customer's original complaint.
- Do not expose private customer information in the reply.
- Follow the four-agent order.
- Do not repeat an agent's work.
"""

        # ----------------------------------------------------
        # STEP 5: RUN THE FOUR-AGENT TEAM
        # ----------------------------------------------------

        team_result = await support_team.run(
            task=initial_task
        )

        messages = team_result.messages

        # ----------------------------------------------------
        # STEP 6: RETRIEVE EACH AGENT'S OUTPUT
        # ----------------------------------------------------

        query_output = get_agent_content(
            messages,
            "customer_query_agent"
        )

        knowledge_output = get_agent_content(
            messages,
            "knowledge_base_agent"
        )

        resolution_output = get_agent_content(
            messages,
            "resolution_agent"
        )

        log_output = get_agent_content(
            messages,
            "log_agent"
        )

        # ----------------------------------------------------
        # STEP 7: PARSE THE QUERY AGENT RESULT
        # ----------------------------------------------------

        analysis = parse_agent_json(
            query_output
        )

        print("\nSTEP 1: CUSTOMER QUERY ANALYSIS")

        print(json.dumps(
            analysis,
            indent=4,
            ensure_ascii=False
        ))

        # ----------------------------------------------------
        # STEP 8: PARSE THE KNOWLEDGE AGENT RESULT
        # ----------------------------------------------------

        knowledge_result = parse_knowledge_result(
            knowledge_output
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
        # STEP 9: PARSE THE RESOLUTION AGENT RESULT
        # ----------------------------------------------------

        resolution = parse_resolution_result(
            resolution_output
        )

        customer_response = resolution["response"]

        confidence = resolution["confidence"]

        confidence_reason = resolution["confidence_reason"]

        print("\nSTEP 3: CUSTOMER SUPPORT RESPONSE")

        print(customer_response)

        print(
            "Resolution confidence:",
            confidence
        )

        print(
            "Confidence reason:",
            confidence_reason
        )

        # ----------------------------------------------------
        # STEP 10: VERIFY ESCALATION DECISION
        # ----------------------------------------------------

        escalation = determine_escalation(
            complaint_text=complaint_text,
            urgency=analysis.get("urgency", ""),
            sentiment=analysis.get("sentiment", ""),
            knowledge_found=knowledge_result["found"],
            resolution_confidence=confidence
        )

        status = (
            "Escalated"
            if escalation["escalated"]
            else "Resolved"
        )

        print("\nSTEP 4: ESCALATION DECISION")

        print(
            "Escalated:",
            escalation["escalated"]
        )

        print(
            "Reasons:",
            escalation["reasons"]
        )

        # ----------------------------------------------------
        # STEP 11: VERIFY LOG AGENT CONFIRMATION
        # ----------------------------------------------------

        log_output = str(log_output)

        if "LOGGED" not in log_output.upper():

            raise RuntimeError(
                "The Log Agent did not confirm successful logging. "
                f"Log Agent output: {log_output}"
            )

        ticket_id = extract_ticket_id(
            log_output
        )

        expected_status = f"Status: {status}"

        if expected_status.lower() not in log_output.lower():

            raise RuntimeError(
                "The Log Agent's status does not match the "
                "escalation decision. "
                f"Expected: {status}. "
                f"Log output: {log_output}"
            )

        print("\nSTEP 5: TICKET LOGGED")

        print("Ticket ID:", ticket_id)

        print("Status:", status)

        # ----------------------------------------------------
        # STEP 12: RETURN RESULTS TO STREAMLIT
        # ----------------------------------------------------

        return {
            "ticket_id": ticket_id,
            "customer_details": customer_details,
            "analysis": analysis,
            "knowledge": knowledge_result,
            "complaint": complaint_text,
            "response": customer_response,
            "complaint_language": complaint_language,           
            "confidence": confidence,
            "confidence_reason": confidence_reason,
            "status": status,
            "escalated": escalation["escalated"],
            "escalation_reasons": escalation["reasons"]
        }

    finally:
        await model_client.close()
