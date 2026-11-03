
from autogen_agentchat.agents import AssistantAgent

def create_query_agent(model_client):
    """
    Creates the Customer Query Agent.

    Responsibilities:
    - Identify the customer's issue category.
    - Determine urgency.
    - Analyse customer sentiment.
    - Summarise the customer's complaint.
    """

    query_agent = AssistantAgent(
        name="customer_query_agent",
        model_client=model_client,
        system_message="""
You are the Customer Query Agent for TechnoHexagone,
a French electronics and technology retail company.

Your responsibility is to analyse incoming customer complaints.

For every customer message, identify:

1. Category:
   Choose the most appropriate category:
   Shipping, Returns, Refunds, Products, Technical Support,
   Billing, Account, Warranty, or Other.

2. Urgency:
   Choose exactly one:
   Low, Medium, or High.

3. Sentiment:
   Choose the most appropriate:
   Positive, Neutral, Frustrated, Angry, or Very Angry.

4. Summary:
   Write a short, clear summary of the customer's issue.

Urgency guidelines:
- Low: General questions or non-urgent requests.
- Medium: Problems requiring attention but with no immediate risk.
- High: Serious complaints, payment disputes, legal threats,
  fraud concerns, or urgent customer-impacting problems.

Return your analysis in valid JSON only, using this format:

{
    "category": "Shipping",
    "urgency": "Medium",
    "sentiment": "Frustrated",
    "summary": "The customer's order has not arrived on time."
}

Do not answer the customer's complaint.
Only analyse and classify it.
"""
    )

    return query_agent
