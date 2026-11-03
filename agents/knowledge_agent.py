
import json
import re
import unicodedata

from pathlib import Path
from collections import Counter

from autogen_agentchat.agents import AssistantAgent


# ============================================================
# KNOWLEDGE BASE SEARCH ENGINE
# ============================================================

class KnowledgeBaseAgent:

    def __init__(self, knowledge_base_path="knowledge_base"):

        path = Path(knowledge_base_path)

        # Resolve relative paths from the project root.
        project_root = Path(__file__).resolve().parents[1]

        if not path.is_absolute():
            current_path = path.resolve()
            project_path = project_root / path

            path = (
                current_path
                if current_path.exists()
                else project_path
            )

        self.knowledge_base_path = path
        self.documents = []

        # ----------------------------------------------------
        # STOP WORDS
        # ----------------------------------------------------

        self.stop_words = {
            # English
            "the", "is", "a", "an", "and", "or", "to", "of",
            "in", "on", "for", "my", "i", "me", "it", "has",
            "have", "been", "was", "are", "with", "but",
            "this", "that", "they", "we", "you", "your",
            "two", "very", "not", "yet", "still", "what",
            "when", "where", "how", "can", "could", "would",
            "please", "help", "need", "want", "customer",
            "hello", "hi", "dear", "ago", "because",
            "nobody", "extremely", "their", "them", "our",
            "after", "before", "from", "about", "there",
            "was", "were", "been", "being", "does", "did",

            # French
            "les", "des", "une", "est", "dans", "sur", "avec",
            "mais", "ce", "cet", "cette", "ces", "mon", "ma",
            "mes", "du", "de", "la", "le", "un", "je", "nous",
            "vous", "pas", "plus", "que", "qui", "quoi",
            "comment", "bonjour", "merci", "pour", "aux",
            "au", "en", "et", "ou", "par", "son", "sa", "ses",
            "ils", "elles", "leur", "leurs", "sont", "ont",
            "etre", "avoir", "peux", "pouvez", "voudrais",
            "mon", "ma", "mes", "notre", "nos", "votre", "vos",
            "qui", "quoi", "quand", "pourquoi", "comment"
        }

        # ----------------------------------------------------
        # SYNONYMS
        # ----------------------------------------------------

        self.synonyms = {

            # Shipping and delivery
            "arrived": ["delivery", "shipping", "parcel"],
            "arrival": ["delivery", "shipping"],
            "delayed": ["delay", "delivery", "shipping"],
            "delay": ["delayed", "delivery", "shipping"],
            "order": ["dispatch", "tracking", "shipment"],
            "ordered": ["order", "dispatch", "shipment"],
            "laptop": ["computer", "product"],
            "missing": ["parcel", "delivery", "shipping"],
            "tracking": ["carrier", "delivery", "shipment"],
            "updates": ["tracking", "carrier", "delivery"],
            "updated": ["tracking", "carrier", "delivery"],
            "shipped": ["dispatch", "shipping", "delivery"],
            "shipment": ["shipping", "delivery", "parcel"],
            "parcel": ["shipping", "delivery", "carrier"],
            "late": ["delayed", "delay", "delivery"],
            "package": ["parcel", "shipping", "delivery"],
            "dispatch": ["shipping", "delivery", "shipment"],

            # Returns and refunds
            "refund": ["reimbursement", "repayment"],
            "refunded": ["refund", "reimbursement"],
            "returned": ["return", "refund"],
            "returning": ["return", "refund"],
            "exchange": ["return", "replacement"],

            # Products
            "broken": ["damaged", "defective", "faulty"],
            "damaged": ["broken", "defective"],
            "faulty": ["broken", "defective", "repair"],
            "defective": ["broken", "faulty", "repair"],

            # Accounts
            "password": ["login", "account", "access"],
            "locked": ["account", "access", "login"],

            # Payments
            "duplicate": ["double", "repeated", "multiple"],
            "charge": ["payment", "billing", "transaction"],
            "payment": ["billing", "transaction", "charge"],

            # Cancellation
            "cancel": ["cancellation", "cancelled"],
            "cancellation": ["cancel", "cancelled"],

            # Warranty
            "warranty": ["guarantee", "repair"],
            "guarantee": ["warranty", "repair"],

            # French and English equivalents
            "reclamation": ["complaint", "problem"],
            "remboursement": ["refund", "repayment"],
            "livraison": ["delivery", "shipping"],
            "retard": ["delay", "delayed"],
            "colis": ["parcel", "package", "delivery"],
            "commande": ["order", "shipment"],
            "panne": ["faulty", "broken", "defective"],
            "motdepasse": ["password", "login", "account"],
            "retour": ["return", "refund"],
            "expedition": ["shipping", "delivery"],
            "paiement": ["payment", "billing"],
            "facturation": ["billing", "payment"],
            "endommage": ["damaged", "broken"],
            "defectueux": ["defective", "faulty"],
            "connexion": ["login", "account", "access"]
        }

        # ----------------------------------------------------
        # CATEGORY-SPECIFIC DOCUMENT FILTERS
        # ----------------------------------------------------

        self.category_filename_keywords = {

            "shipping": {
                "shipping", "delivery", "carrier",
                "tracking", "dispatch", "shipment",
                "parcel"
            },

            "returns": {
                "return", "returns", "exchange"
            },

            "refunds": {
                "refund", "refunds", "reimbursement"
            },

            "products": {
                "product", "products", "electronics",
                "laptop", "computer", "device"
            },

            "technical support": {
                "troubleshooting", "technical",
                "repair", "fault", "error",
                "overheating", "setup"
            },

            "billing": {
                "billing", "payment", "invoice",
                "charge", "transaction"
            },

            "account": {
                "account", "login", "password",
                "access", "signin"
            },

            "warranty": {
                "warranty", "guarantee"
            }
        }

        self.category_content_keywords = {

            "shipping": {
                "shipping", "delivery", "carrier",
                "tracking", "dispatch", "shipment",
                "parcel", "courier", "transit",
                "delayed", "delay"
            },

            "returns": {
                "return", "returns", "exchange",
                "replacement", "refund"
            },

            "refunds": {
                "refund", "refunds", "reimbursement",
                "repayment", "returned"
            },

            "products": {
                "product", "electronics",
                "computer", "laptop", "device",
                "phone", "blender"
            },

            "technical support": {
                "troubleshooting", "technical",
                "repair", "fault", "error",
                "overheating", "malfunction",
                "reset", "defective"
            },

            "billing": {
                "billing", "payment", "invoice",
                "charge", "transaction", "card"
            },

            "account": {
                "account", "login", "password",
                "access", "signin", "credentials"
            },

            "warranty": {
                "warranty", "guarantee",
                "repair", "coverage"
            }
        }

        self.load_documents()

    # ========================================================
    # TEXT NORMALISATION
    # ========================================================

    @staticmethod
    def normalize_text(text):
        """Normalise text and remove accents."""

        text = str(text).lower()

        text = unicodedata.normalize(
            "NFKD",
            text
        )

        text = "".join(
            character
            for character in text
            if not unicodedata.combining(character)
        )

        return text

    def tokenize(self, text):
        """Extract useful words from text."""

        normalized = self.normalize_text(text)

        words = re.findall(
            r"\b[a-z0-9]+\b",
            normalized
        )

        return [
            word for word in words
            if len(word) > 2
            and word not in self.stop_words
        ]

    # ========================================================
    # LOAD DOCUMENTS
    # ========================================================

    def load_documents(self):
        """Load Markdown documents from the knowledge base."""

        if not self.knowledge_base_path.exists():
            raise FileNotFoundError(
                f"Knowledge base folder not found: "
                f"{self.knowledge_base_path}"
            )

        self.documents = []

        for file_path in sorted(
            self.knowledge_base_path.glob("*.md")
        ):

            content = file_path.read_text(
                encoding="utf-8"
            )

            normalized_content = self.normalize_text(
                content
            )

            self.documents.append({
                "filename": file_path.name,
                "content": content,
                "normalized_content": normalized_content
            })

        if not self.documents:
            raise ValueError(
                "No Markdown documents were found "
                "in the knowledge base."
            )

        print(
            f"Loaded {len(self.documents)} "
            "knowledge-base documents."
        )

    # ========================================================
    # KEYWORD EXPANSION
    # ========================================================

    def expand_keywords(self, keywords):
        """Expand customer keywords using synonyms."""

        expanded = set(keywords)

        for keyword in keywords:
            expanded.update(
                self.synonyms.get(keyword, [])
            )

        return expanded

    # ========================================================
    # CATEGORY FILTER
    # ========================================================

    def document_matches_category(
        self,
        filename,
        content_words,
        category
    ):
        """
        Check whether a document genuinely belongs
        to the requested complaint category.

        A filename match is the strongest signal.
        Otherwise, several category-specific content
        keywords must be present.
        """

        category = self.normalize_text(
            category
        ).strip()

        filename_words = set(
            self.tokenize(
                filename.replace("_", " ")
            )
        )

        filename_keywords = (
            self.category_filename_keywords.get(
                category
            )
        )

        content_keywords = (
            self.category_content_keywords.get(
                category
            )
        )

        # Unknown categories do not apply a strict filter.
        if not filename_keywords or not content_keywords:
            return True, set(), set()

        filename_matches = (
            filename_words & filename_keywords
        )

        content_matches = (
            content_words & content_keywords
        )

        # A category-specific filename is strong evidence.
        if filename_matches:
            return True, filename_matches, content_matches

        # Otherwise require at least three distinct
        # category-specific terms in the document.
        if len(content_matches) >= 3:
            return True, filename_matches, content_matches

        return False, filename_matches, content_matches

    # ========================================================
    # DOCUMENT SEARCH
    # ========================================================

    def search(
        self,
        query,
        top_k=3,
        min_score=2,
        category=None
    ):
        """Find and rank category-relevant documents."""

        if (
            not isinstance(query, str)
            or not query.strip()
            or top_k < 1
        ):
            return []

        # Include the category as an additional search signal.
        search_query = (
            f"{category} {query}"
            if category
            else query
        )

        query_keywords = self.tokenize(
            search_query
        )

        if not query_keywords:
            return []

        query_counts = Counter(query_keywords)

        expanded_keywords = self.expand_keywords(
            query_counts.keys()
        )

        results = []

        # Identify gift-card questions.
        gift_card_query = (
            "gift" in query_keywords
            or "giftcard" in query_keywords
        )

        for document in self.documents:

            filename = self.normalize_text(
                document["filename"].replace("_", " ")
            )

            content = document["normalized_content"]

            filename_words = set(
                self.tokenize(filename)
            )

            content_words = set(
                self.tokenize(content)
            )

            # Strict category filtering.
            category_match, filename_category_matches, content_category_matches = (
                self.document_matches_category(
                    document["filename"],
                    content_words,
                    category or ""
                )
            )

            if not category_match:
                continue

            # Direct matches.
            direct_matches = (
                set(query_counts.keys()) & content_words
            )

            score = 0

            for keyword in direct_matches:
                score += min(
                    query_counts[keyword],
                    3
                ) * 3

            # Synonym matches.
            related_matches = (
                expanded_keywords
                - set(query_counts.keys())
            ) & content_words

            score += len(related_matches)

            # Filename relevance.
            filename_matches = (
                expanded_keywords & filename_words
            )

            score += len(filename_matches) * 5

            # Give additional weight to category-specific filenames.
            score += len(filename_category_matches) * 8

            # Give a smaller boost to category-specific content.
            score += len(content_category_matches) * 2

            # Keyword coverage.
            coverage = (
                len(direct_matches)
                / max(len(query_counts), 1)
            )

            score += coverage * 2

            # Minimum relevance requirement.
            relevant_enough = (
                len(direct_matches) >= 2
                or (
                    len(direct_matches) >= 1
                    and (
                        len(related_matches) >= 2
                        or bool(filename_category_matches)
                    )
                )
            )

            # Gift-card safeguard.
            if gift_card_query:

                document_mentions_gift_card = (
                    "gift card" in content
                    or "gift-card" in content
                    or "giftcard" in content
                )

                if not document_mentions_gift_card:
                    relevant_enough = False

            if relevant_enough and score >= min_score:

                results.append({
                    "filename": document["filename"],
                    "content": document["content"],
                    "score": round(score, 2),
                    "coverage": round(coverage, 2)
                })

        # Highest relevance first.
        results.sort(
            key=lambda item: (
                item["score"],
                item["coverage"]
            ),
            reverse=True
        )

        return results[:top_k]

    # ========================================================
    # GET KNOWLEDGE
    # ========================================================

    def get_knowledge(
        self,
        query,
        category=None
    ):
        """Return retrieved passages and source filenames."""

        results = self.search(
            query,
            top_k=3,
            min_score=2,
            category=category
        )

        if not results:
            return {
                "found": False,
                "sources": [],
                "knowledge": (
                    "No sufficiently relevant information "
                    "was found in the company knowledge base. "
                    "Human support may need to investigate."
                )
            }

        knowledge_sections = []

        for result in results:

            knowledge_sections.append(
                f"SOURCE: {result['filename']}\n"
                f"{result['content']}"
            )

        return {
            "found": True,
            "sources": [
                result["filename"]
                for result in results
            ],
            "knowledge": "\n\n".join(
                knowledge_sections
            )
        }


# ============================================================
# AUTOGEN KNOWLEDGE BASE AGENT
# ============================================================

def create_knowledge_agent(
    model_client,
    knowledge_base_path="knowledge_base"
):
    """
    Create the AutoGen Knowledge Base AssistantAgent.

    The Python search engine is exposed as a tool.
    """

    knowledge_base = KnowledgeBaseAgent(
        knowledge_base_path
    )

    def search_company_knowledge(
        query: str,
        category: str = "Other"
    ) -> str:
        """
        Search TechnoHexagone documents using the complaint
        and its classification.

        Returns JSON containing found, sources and knowledge.
        """

        result = knowledge_base.get_knowledge(
            query,
            category=category
        )

        return json.dumps(
            result,
            ensure_ascii=False,
            indent=4
        )

    knowledge_agent = AssistantAgent(
        name="knowledge_base_agent",

        description=(
            "Searches TechnoHexagone company documents "
            "and retrieves category-relevant information and sources."
        ),

        model_client=model_client,

        tools=[
            search_company_knowledge
        ],

        max_tool_iterations=1,

        reflect_on_tool_use=False,

        system_message="""
You are the Knowledge Base Agent for TechnoHexagone.

YOUR RESPONSIBILITY:

Find relevant information in the company's local
Markdown knowledge-base documents.

TOOL USAGE:

You MUST call the search_company_knowledge tool
for every customer complaint.

Use the Query Agent's category exactly as returned.

Pass these two arguments:

1. query:
   Include the customer's actual complaint and the
   Query Agent's summary. Use meaningful details.
   Do not add unrelated topics.

2. category:
   Pass the Query Agent's exact category.

CATEGORY ACCURACY:

The category is important.

For example:
- Shipping complaints must search shipping documents.
- Returns complaints must search return documents.
- Billing complaints must search billing documents.
- Account complaints must search account documents.
- Technical Support complaints must search technical documents.

Do not return documents from an unrelated category
just because they mention a similar product or keyword.

SEARCH RESULTS:

The tool returns JSON containing:
- found
- sources
- knowledge

If found is false:
- Report that no sufficiently relevant document was found.
- Do not invent an answer.

OUTPUT:

- Return the JSON result from the tool.
- Preserve source filenames exactly.
- Do not add unrelated information.
- Do not answer the customer directly.
- Do not generate the final customer response.
"""
    )

    return knowledge_agent
