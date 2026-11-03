import asyncio
import html
import re
from pathlib import Path

import pandas as pd
import streamlit as st

from team import process_customer_query


# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="TechnoHexagone | AI Customer Support Desk",
    page_icon="🟠",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
LOG_FILE = BASE_DIR / "logs" / "tickets.csv"
KB_DIR = BASE_DIR / "knowledge_base"
CSS_FILE = BASE_DIR / "styles" / "style.css"

if CSS_FILE.exists():
    st.markdown(
        f"<style>{CSS_FILE.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )


# =========================================================
# TRANSLATIONS
# =========================================================
TRANSLATIONS = {
    "English": {
        "language": "Website language",
        "workspace": "WORKSPACE",
        "overview": "Overview",
        "new_complaint": "✚ New Complaint",
        "latest_result": "✓ Latest Result",
        "ticket_history": "Ticket History",
        "knowledge_base": "Knowledge Base",
        "about": "About",
        "agents": "OUR AI AGENTS",
        "query_agent": "Query Agent",
        "query_desc": "Classifies the complaint",
        "kb_agent": "Knowledge Base Agent",
        "kb_desc": "Finds company policies",
        "resolution_agent": "Resolution Agent",
        "resolution_desc": "Generates customer response",
        "log_agent": "Log Agent",
        "log_desc": "Records the ticket",
        "system_ready": "AI Support System",
        "ready_desc": "Ready to process customer requests",
        "eyebrow": "TECHNOHEXAGONE CUSTOMER SUPPORT",
        "app_title": "AI Customer Support Desk",
        "powered": "Powered by Multi-Agent AI",
        "welcome": "Welcome to TechnoHexagone",
        "welcome_desc": "Manage customer requests, monitor support activity and review AI-assisted resolutions.",
        "support_overview": "Support overview",
        "total_tickets": "Total tickets",
        "resolved_tickets": "Resolved tickets",
        "pending_tickets": "Pending tickets",
        "escalated_tickets": "Escalated tickets",
        "new_customer_tickets": "New-customer tickets",
        "recent_activity": "Recent support activity",
        "distribution": "Ticket distribution",
        "no_tickets": "No support tickets have been submitted yet.",
        "no_stats": "Ticket category statistics will appear here.",
        "quick_actions": "Quick actions",
        "new_complaint_title": "✚ New complaint",
        "new_complaint_desc": "Register a new customer support request.",
        "create_complaint": "Create complaint",
        "ticket_management": "▤ Ticket management",
        "ticket_management_desc": "Review customer tickets and escalation status.",
        "view_all_tickets": "View all tickets",
        "kb_title": "📚 Knowledge base",
        "documents_available": "company documents available.",
        "explore_documents": "Explore documents",
        "step1_heading": "New customer complaint",
        "step1_subtitle": "Step 1 of 2 — Tell us how we can identify and contact you.",
        "step1_label": "STEP 1 · CUSTOMER DETAILS",
        "contact_info": "Your contact information",
        "contact_desc": "Complete your details first. Your information will be attached to your support ticket.",
        "progress1": "Step 1 of 2 · Customer details",
        "customer_type": "Customer type",
        "new": "New",
        "existing": "Existing",
        "full_name": "Full name *",
        "name_placeholder": "Enter your full name",
        "email": "Email address *",
        "email_placeholder": "example@email.com",
        "phone": "Contact number",
        "phone_placeholder": "+33 6 00 00 00 00",
        "phone_help": "Enter 7 to 15 digits. You may use +, spaces, hyphens and parentheses.",
        "client_id": "Client ID",
        "client_placeholder": "Enter your client ID",
        "client_help": "Required for existing customers. This demo records the ID but does not validate it against a customer database.",
        "order_id": "Order ID (optional)",
        "order_placeholder": "e.g. TH-2026-00125",
        "continue": "Continue to complaint details →",
        "name_error": "Please enter your full name.",
        "email_error": "Please enter a valid email address.",
        "phone_error": "Please enter a valid phone number using 7 to 15 digits. Letters are not allowed.",
        "client_error": "Please enter your Client ID for an existing customer.",
        "step2_subtitle": "Step 2 of 2 — Describe the issue so our AI agents can help.",
        "progress2": "Step 2 of 2 · Complaint details",
        "customer_details": "Customer details",
        "name": "Name",
        "category": "Complaint category *",
        "select_category": "Select a category",
        "describe_issue": "Describe your issue *",
        "complaint_placeholder": "Tell us what happened, when it happened and how we can help...",
        "back": "← Back to customer details",
        "submit": "Submit complaint and get AI response",
        "category_error": "Please select a complaint category.",
        "complaint_error": "Please describe your issue.",
        "processing": "Our AI agents are analysing your complaint...",
        "processing_error": "We could not process your request. Please check the application terminal for details.",
        "processed": "Your support request has been processed",
        "recorded": "Your complaint has been recorded. Your AI-generated response is shown below.",
        "ticket_id": "Ticket ID",
        "urgency": "Urgency",
        "status": "Status",
        "support_response": "Customer support response",
        "customer_request": "Customer request",
        "keep_ticket": "Please keep your ticket ID. If your request requires human assistance, our support team will follow up using the contact details you provided.",
        "download_response": "↓ Download customer response",
        "escalation_status": "Escalation status",
        "requires_human": "This request requires human support.",
        "no_escalation": "No human-support escalation was triggered.",
        "analysis_sources": "View AI analysis and knowledge-base sources",
        "sentiment": "Sentiment",
        "summary": "Summary",
        "sources": "Knowledge-base sources",
        "no_sources": "No source documents found.",
        "retrieved": "Retrieved information",
        "another_complaint": "＋ Submit another complaint",
        "view_history": "View ticket history",
        "history_title": "Ticket History",
        "history_subtitle": "Review and download previously submitted customer support tickets.",
        "search_tickets": "Search tickets",
        "search_placeholder": "Search ticket ID, customer name, email or category...",
        "tickets_found": "ticket(s) found.",
        "download_history": "Download ticket history (CSV)",
        "no_history": "No tickets are available yet.",
        "kb_page_title": "Company Knowledge Base",
        "kb_page_subtitle": "Browse the company documents used by the Knowledge Base Agent.",
        "available_docs": "Available documents",
        "select_doc": "Select a document",
        "no_docs": "No Markdown documents were found in the knowledge_base folder.",
        "about_title": "About TechnoHexagone Support",
        "about_subtitle": "An AI-powered customer support demonstration built with four specialised agents.",
        "about_text": "TechnoHexagone is a fictional French electronics retailer. This application demonstrates an AI-powered multi-agent customer support system.",
        "our_agents": "Our four specialised AI agents",
        "query_about": "Classifies the complaint, urgency and customer sentiment.",
        "kb_about": "Searches company documents and retrieves relevant policy information.",
        "resolution_about": "Creates a customer-ready response using retrieved company information.",
        "log_about": "Records tickets and tracks escalation status.",
        "technology": "Technology",
        "technology_list": "- Python\n- AutoGen multi-agent framework\n- Streamlit\n- Company Markdown knowledge base\n- CSV ticket logging",
        "go_overview": "Go to overview",
        "category_shipping": "Shipping",
        "category_returns": "Returns",
        "category_refunds": "Refunds",
        "category_products": "Products",
        "category_technical": "Technical Support",
        "category_billing": "Billing",
        "category_account": "Account",
        "category_warranty": "Warranty",
        "category_other": "Other",
    },
    "Français": {
        "language": "Langue du site",
        "workspace": "ESPACE DE TRAVAIL",
        "overview": "Vue d'ensemble",
        "new_complaint": "✚ Nouvelle réclamation",
        "latest_result": "✓ Dernier résultat",
        "ticket_history": "Historique des tickets",
        "knowledge_base": "Base de connaissances",
        "about": "À propos",
        "agents": "NOS AGENTS IA",
        "query_agent": "Agent de requête",
        "query_desc": "Classe la réclamation",
        "kb_agent": "Agent base de connaissances",
        "kb_desc": "Recherche les politiques de l'entreprise",
        "resolution_agent": "Agent de résolution",
        "resolution_desc": "Rédige la réponse au client",
        "log_agent": "Agent de journalisation",
        "log_desc": "Enregistre le ticket",
        "system_ready": "Système d'assistance IA",
        "ready_desc": "Prêt à traiter les demandes des clients",
        "eyebrow": "SERVICE CLIENT TECHNOHEXAGONE",
        "app_title": "Service client IA",
        "powered": "Propulsé par une IA multi-agents",
        "welcome": "Bienvenue chez TechnoHexagone",
        "welcome_desc": "Gérez les demandes clients, suivez l'activité du support et consultez les résolutions assistées par IA.",
        "support_overview": "Vue d'ensemble du support",
        "total_tickets": "Nombre total de tickets",
        "resolved_tickets": "Tickets résolus",
        "pending_tickets": "Tickets en attente",
        "escalated_tickets": "Tickets escaladés",
        "new_customer_tickets": "Tickets nouveaux clients",
        "recent_activity": "Activité récente du support",
        "distribution": "Répartition des tickets",
        "no_tickets": "Aucun ticket n'a encore été soumis.",
        "no_stats": "Les statistiques par catégorie apparaîtront ici.",
        "quick_actions": "Actions rapides",
        "new_complaint_title": "✚ Nouvelle réclamation",
        "new_complaint_desc": "Enregistrer une nouvelle demande d'assistance.",
        "create_complaint": "Créer une réclamation",
        "ticket_management": "▤ Gestion des tickets",
        "ticket_management_desc": "Consulter les tickets clients et leur statut d'escalade.",
        "view_all_tickets": "Voir tous les tickets",
        "kb_title": "📚 Base de connaissances",
        "documents_available": "documents de l'entreprise disponibles.",
        "explore_documents": "Explorer les documents",
        "step1_heading": "Nouvelle réclamation client",
        "step1_subtitle": "Étape 1 sur 2 — Indiquez comment nous pouvons vous identifier et vous contacter.",
        "step1_label": "ÉTAPE 1 · COORDONNÉES CLIENT",
        "contact_info": "Vos coordonnées",
        "contact_desc": "Renseignez vos informations. Elles seront associées à votre ticket d'assistance.",
        "progress1": "Étape 1 sur 2 · Coordonnées",
        "customer_type": "Type de client",
        "new": "Nouveau",
        "existing": "Existant",
        "full_name": "Nom complet *",
        "name_placeholder": "Saisissez votre nom complet",
        "email": "Adresse e-mail *",
        "email_placeholder": "exemple@email.com",
        "phone": "Numéro de téléphone",
        "phone_placeholder": "+33 6 00 00 00 00",
        "phone_help": "Saisissez 7 à 15 chiffres. Vous pouvez utiliser +, espaces, tirets et parenthèses.",
        "client_id": "Identifiant client",
        "client_placeholder": "Saisissez votre identifiant client",
        "client_help": "Obligatoire pour les clients existants. Cette démonstration enregistre l'identifiant sans le vérifier dans une base clients.",
        "order_id": "Numéro de commande (facultatif)",
        "order_placeholder": "ex. TH-2026-00125",
        "continue": "Continuer vers les détails de la réclamation →",
        "name_error": "Veuillez saisir votre nom complet.",
        "email_error": "Veuillez saisir une adresse e-mail valide.",
        "phone_error": "Veuillez saisir un numéro valide comportant 7 à 15 chiffres. Les lettres ne sont pas autorisées.",
        "client_error": "Veuillez saisir votre identifiant client.",
        "step2_subtitle": "Étape 2 sur 2 — Décrivez le problème afin que nos agents IA puissent vous aider.",
        "progress2": "Étape 2 sur 2 · Détails de la réclamation",
        "customer_details": "Coordonnées du client",
        "name": "Nom",
        "category": "Catégorie de réclamation *",
        "select_category": "Sélectionnez une catégorie",
        "describe_issue": "Décrivez votre problème *",
        "complaint_placeholder": "Expliquez ce qui s'est passé, quand et comment nous pouvons vous aider...",
        "back": "← Retour aux coordonnées",
        "submit": "Envoyer la réclamation et obtenir une réponse IA",
        "category_error": "Veuillez sélectionner une catégorie.",
        "complaint_error": "Veuillez décrire votre problème.",
        "processing": "Nos agents IA analysent votre réclamation...",
        "processing_error": "Impossible de traiter votre demande. Consultez le terminal de l'application pour plus de détails.",
        "processed": "Votre demande d'assistance a été traitée",
        "recorded": "Votre réclamation a été enregistrée. La réponse générée par l'IA est affichée ci-dessous.",
        "ticket_id": "Numéro du ticket",
        "urgency": "Urgence",
        "status": "Statut",
        "support_response": "Réponse du service client",
        "customer_request": "Demande du client",
        "keep_ticket": "Conservez votre numéro de ticket. Si une assistance humaine est nécessaire, notre équipe vous recontactera avec les coordonnées fournies.",
        "download_response": "↓ Télécharger la réponse client",
        "escalation_status": "Statut de l'escalade",
        "requires_human": "Cette demande nécessite l'intervention du service client.",
        "no_escalation": "Aucune escalade vers un agent humain n'a été déclenchée.",
        "analysis_sources": "Voir l'analyse IA et les sources de la base de connaissances",
        "sentiment": "Sentiment",
        "summary": "Résumé",
        "sources": "Sources de la base de connaissances",
        "no_sources": "Aucun document source trouvé.",
        "retrieved": "Informations récupérées",
        "another_complaint": "＋ Soumettre une autre réclamation",
        "view_history": "Voir l'historique des tickets",
        "history_title": "Historique des tickets",
        "history_subtitle": "Consultez et téléchargez les tickets d'assistance précédemment soumis.",
        "search_tickets": "Rechercher des tickets",
        "search_placeholder": "Rechercher par numéro, nom, e-mail ou catégorie...",
        "tickets_found": "ticket(s) trouvé(s).",
        "download_history": "Télécharger l'historique des tickets (CSV)",
        "no_history": "Aucun ticket disponible pour le moment.",
        "kb_page_title": "Base de connaissances de l'entreprise",
        "kb_page_subtitle": "Parcourez les documents utilisés par l'agent de la base de connaissances.",
        "available_docs": "Documents disponibles",
        "select_doc": "Sélectionner un document",
        "no_docs": "Aucun document Markdown trouvé dans le dossier knowledge_base.",
        "about_title": "À propos du support TechnoHexagone",
        "about_subtitle": "Démonstration d'un service client IA reposant sur quatre agents spécialisés.",
        "about_text": "TechnoHexagone est un détaillant fictif français de produits électroniques. Cette application présente un système de support client multi-agents basé sur l'IA.",
        "our_agents": "Nos quatre agents spécialisés",
        "query_about": "Classe la réclamation, son urgence et le sentiment du client.",
        "kb_about": "Recherche les documents de l'entreprise et les informations pertinentes des politiques.",
        "resolution_about": "Rédige une réponse destinée au client à partir des informations récupérées.",
        "log_about": "Enregistre les tickets et suit leur statut d'escalade.",
        "technology": "Technologies",
        "technology_list": "- Python\n- Framework multi-agents AutoGen\n- Streamlit\n- Base de connaissances Markdown\n- Journalisation des tickets CSV",
        "go_overview": "Retour à la vue d'ensemble",
        "category_shipping": "Livraison",
        "category_returns": "Retours",
        "category_refunds": "Remboursements",
        "category_products": "Produits",
        "category_technical": "Assistance technique",
        "category_billing": "Facturation",
        "category_account": "Compte",
        "category_warranty": "Garantie",
        "category_other": "Autre",
    },
}

CATEGORY_KEYS = {
    "Shipping": "category_shipping",
    "Returns": "category_returns",
    "Refunds": "category_refunds",
    "Products": "category_products",
    "Technical Support": "category_technical",
    "Billing": "category_billing",
    "Account": "category_account",
    "Warranty": "category_warranty",
    "Other": "category_other",
}

# Keep the language choice across Streamlit reruns.
if "website_language" not in st.session_state:
    st.session_state.website_language = "English"

def tr(key):
    return TRANSLATIONS[st.session_state.website_language].get(
        key, TRANSLATIONS["English"].get(key, key)
    )


# =========================================================
# SESSION STATE
# =========================================================
DEFAULTS = {
    "page": "Overview",
    "latest_result": None,
    "customer_details_draft": {},
    "complaint_category_draft": "",
    "complaint_text_draft": "",
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# HELPERS
# =========================================================
def get_image_path(filename):
    path = ASSETS_DIR / filename
    return str(path) if path.exists() else None


def show_image(filename, **kwargs):
    image_path = get_image_path(filename)
    if image_path:
        st.image(image_path, **kwargs)
        return True
    return False


def load_tickets():
    if not LOG_FILE.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(LOG_FILE).fillna("")
    except (pd.errors.EmptyDataError, PermissionError, OSError, UnicodeDecodeError):
        return pd.DataFrame()


def safe_value(value, default="—"):
    if value is None:
        return default
    try:
        if pd.isna(value) or str(value).strip() == "":
            return default
    except (TypeError, ValueError):
        pass
    return str(value)


def email_is_valid(email):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()))


def phone_is_valid(phone):
    """Allow common international phone formatting, but no alphabetic characters."""
    if not phone or not phone.strip():
        return True  # Phone number is optional.
    value = phone.strip()
    if not re.fullmatch(r"\+?[0-9\s().-]+", value):
        return False
    digits = re.sub(r"\D", "", value)
    return 7 <= len(digits) <= 15


def navigate(page):
    st.session_state.page = page
    st.rerun()


def start_new_complaint():
    st.session_state.customer_details_draft = {}
    st.session_state.complaint_category_draft = ""
    st.session_state.complaint_text_draft = ""
    st.session_state.page = "New Complaint — Step 1"
    st.rerun()


def page_heading(title, subtitle, icon=""):
    st.markdown(
        f"""
        <div class="page-heading">
            <div class="page-heading-icon">{icon}</div>
            <div>
                <h2>{html.escape(title)}</h2>
                <p>{html.escape(subtitle)}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_latest_result(result):
    analysis = result.get("analysis", {})
    knowledge = result.get("knowledge", {})
    customer = result.get("customer_details", {})
    response = result.get("response", "No response was generated.")
    complaint = result.get("complaint", "")

    st.markdown(f"## {tr('processed')}")
    st.success(tr("recorded"))

    metric_cols = st.columns(4)
    metric_values = [
        (tr("ticket_id"), result.get("ticket_id", "—")),
        (tr("category"), analysis.get("category", "—")),
        (tr("urgency"), analysis.get("urgency", "—")),
        (tr("status"), result.get("status", "—")),
    ]
    for col, (label, value) in zip(metric_cols, metric_values):
        with col:
            st.metric(label, str(value))

    # Display the original customer request.
    if complaint:
        st.markdown(f"### {tr('customer_request')}")
        st.markdown(
            f'<div class="response-card">'
            f'{html.escape(complaint).replace(chr(10), "<br>")}'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown(f"### {tr('support_response')}")
    st.caption(tr("keep_ticket"))
    st.markdown(
        f'<div class="response-card">{html.escape(response).replace(chr(10), "<br>")}</div>',
        unsafe_allow_html=True,
    )
    st.download_button(
        tr("download_response"),
        data=response,
        file_name=f"{result.get('ticket_id', 'support_response')}_response.txt",
        mime="text/plain",
        use_container_width=False,
        key="download_latest_response",
    )

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown(f"#### {tr('customer_details')}")
            st.write(f"**{tr('name')}:** {safe_value(customer.get('customer_name'))}")
            st.write(f"**{tr('email')}:** {safe_value(customer.get('email'))}")
            st.write(f"**{tr('order_id')}:** {safe_value(customer.get('order_id'))}")
            st.write(f"**{tr('ticket_id')}:** `{result.get('ticket_id', '—')}`")
    with right:
        with st.container(border=True):
            st.markdown(f"#### {tr('escalation_status')}")
            if result.get("escalated"):
                st.warning(tr("requires_human"))
                for reason in result.get("escalation_reasons", []):
                    st.write(f"• {reason}")
            else:
                st.success(tr("no_escalation"))

    with st.expander(tr("analysis_sources")):
        st.markdown(f"**{tr('category')}:** " + safe_value(analysis.get("category")))
        st.markdown(f"**{tr('urgency')}:** " + safe_value(analysis.get("urgency")))
        st.markdown(f"**{tr('sentiment')}:** " + safe_value(analysis.get("sentiment")))
        st.markdown(f"**{tr('summary')}:** " + safe_value(analysis.get("summary")))
        st.markdown(f"**{tr('sources')}**")
        sources = knowledge.get("sources", [])
        if sources:
            for source in sources:
                st.write(f"📄 {source}")
        else:
            st.write(tr("no_sources"))
        if knowledge.get("knowledge"):
            st.markdown(f"**{tr('retrieved')}**")
            st.write(knowledge["knowledge"])

    button_col1, button_col2 = st.columns(2)
    with button_col1:
        if st.button(tr("another_complaint"), type="primary", use_container_width=True):
            start_new_complaint()
    with button_col2:
        if st.button(tr("view_history"), use_container_width=True):
            navigate("Ticket History")


# =========================================================
# SIDEBAR NAVIGATION + LANGUAGE SELECTOR
# =========================================================
with st.sidebar:
    logo = get_image_path("logo_wordmark.png")
    if logo:
        st.image(logo, use_container_width=True)
    else:
        st.markdown(
            '<div class="sidebar-brand">🟠 TechnoHexagone</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<p class="sidebar-caption">CUSTOMER SUPPORT CENTRE</p>',
        unsafe_allow_html=True,
    )

    st.selectbox(
        tr("language"),
        ["English", "Français"],
        key="website_language",
        format_func=lambda value: "English" if value == "English" else "Français",
    )
    st.divider()
    st.markdown(f"### {tr('workspace')}")

    current_page = st.session_state.page
    nav_items = [
        ("Overview", "🏠", tr("overview")),
        ("New Complaint — Step 1", "✚", tr("new_complaint")),
        ("Ticket History", "▤", tr("ticket_history")),
        ("Knowledge Base", "📚", tr("knowledge_base")),
        ("About", "ⓘ", tr("about")),
    ]
    if st.session_state.latest_result:
        nav_items.insert(2, ("Latest Result", "✓", tr("latest_result")))

    for page_name, _icon, label in nav_items:
        is_active = (
            current_page == page_name
            or (
                page_name == "New Complaint — Step 1"
                and current_page == "New Complaint — Step 2"
            )
        )
        if st.button(
            label,
            key=f"nav_{page_name}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            if page_name == "New Complaint — Step 1":
                start_new_complaint()
            else:
                navigate(page_name)

    st.divider()
    st.markdown(f"### {tr('agents')}")
    agents = [
        ("01", tr("query_agent"), tr("query_desc")),
        ("02", tr("kb_agent"), tr("kb_desc")),
        ("03", tr("resolution_agent"), tr("resolution_desc")),
        ("04", tr("log_agent"), tr("log_desc")),
    ]
    for number, name, description in agents:
        st.markdown(
            f"""
            <div class="sidebar-agent">
                <span class="agent-number">{number}</span>
                <div><strong>{html.escape(name)}</strong><small>{html.escape(description)}</small></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown(
        f"""
        <div class="sidebar-status">
            <span class="online-dot"></span> {tr('system_ready')}
            <br><small>{tr('ready_desc')}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# MAIN HEADER
# =========================================================
header_title, header_image = st.columns([3, 1.15], vertical_alignment="center")
with header_title:
    st.markdown(
        f"""
        <div class="main-title">
            <div class="eyebrow">{tr('eyebrow')}</div>
            <h1>{tr('app_title')}</h1>
            <p>{tr('powered')}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with header_image:
    show_image("electronics_banner.png", use_container_width=True)

st.markdown('<div class="top-divider"></div>', unsafe_allow_html=True)


# =========================================================
# OVERVIEW
# =========================================================
if st.session_state.page == "Overview":
    tickets = load_tickets()
    total_tickets = len(tickets)

    if not tickets.empty:
        resolved_tickets = (
            tickets["Status"].astype(str).str.lower().eq("resolved").sum()
            if "Status" in tickets.columns else 0
        )
        pending_tickets = (
            tickets["Status"].astype(str).str.lower().eq("pending").sum()
            if "Status" in tickets.columns else 0
        )
        escalated_tickets = (
            tickets["Escalated"].astype(str).str.lower().isin(["true", "1", "yes"]).sum()
            if "Escalated" in tickets.columns else 0
        )
        new_customer_tickets = (
            tickets["Customer_Type"].astype(str).str.lower().eq("new").sum()
            if "Customer_Type" in tickets.columns else 0
        )
    else:
        resolved_tickets = pending_tickets = escalated_tickets = new_customer_tickets = 0

    welcome_col, illustration_col = st.columns([3, 1.05], vertical_alignment="center")
    with welcome_col:
        st.markdown(
            f"""
            <div class="welcome-panel">
                <div class="welcome-label">{tr('eyebrow')}</div>
                <h2>{tr('welcome')}</h2>
                <p>{tr('welcome_desc')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with illustration_col:
        show_image("support_agent_illustration.png", use_container_width=True)

    st.markdown(f"## {tr('support_overview')}")
    metric_cols = st.columns(5)
    metrics = [
        (tr("total_tickets"), total_tickets),
        (tr("resolved_tickets"), resolved_tickets),
        (tr("pending_tickets"), pending_tickets),
        (tr("escalated_tickets"), escalated_tickets),
        (tr("new_customer_tickets"), new_customer_tickets),
    ]
    for col, (label, value) in zip(metric_cols, metrics):
        with col:
            st.metric(label, int(value))

    activity_col, distribution_col = st.columns([1.7, 1])
    with activity_col:
        st.markdown(f"### {tr('recent_activity')}")
        if not tickets.empty:
            display_columns = [
                c for c in [
                    "Ticket_ID", "Customer_Name", "Category",
                    "Urgency", "Status", "Escalated",
                ] if c in tickets.columns
            ]
            st.dataframe(
                tickets[display_columns].tail(6).iloc[::-1],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info(tr("no_tickets"))

    with distribution_col:
        st.markdown(f"### {tr('distribution')}")
        if not tickets.empty and "Category" in tickets.columns:
            counts = tickets["Category"].replace("", "Other").fillna("Other").value_counts()
            st.bar_chart(counts, color="#F28C28")
        else:
            st.info(tr("no_stats"))

    st.divider()
    st.markdown(f"### {tr('quick_actions')}")
    action_cols = st.columns(3)
    with action_cols[0]:
        st.markdown(
            f'<div class="action-card"><h3>{tr("new_complaint_title")}</h3>'
            f'<p>{tr("new_complaint_desc")}</p></div>',
            unsafe_allow_html=True,
        )
        if st.button(tr("create_complaint"), use_container_width=True):
            start_new_complaint()
    with action_cols[1]:
        st.markdown(
            f'<div class="action-card"><h3>{tr("ticket_management")}</h3>'
            f'<p>{tr("ticket_management_desc")}</p></div>',
            unsafe_allow_html=True,
        )
        if st.button(tr("view_all_tickets"), use_container_width=True):
            navigate("Ticket History")
    with action_cols[2]:
        kb_count = len(list(KB_DIR.glob("*.md"))) if KB_DIR.exists() else 0
        st.markdown(
            f'<div class="action-card"><h3>{tr("kb_title")}</h3>'
            f'<p>{kb_count} {tr("documents_available")}</p></div>',
            unsafe_allow_html=True,
        )
        if st.button(tr("explore_documents"), use_container_width=True):
            navigate("Knowledge Base")


# =========================================================
# NEW COMPLAINT — STEP 1
# =========================================================
elif st.session_state.page == "New Complaint — Step 1":
    page_heading(tr("step1_heading"), tr("step1_subtitle"), "✚")
    st.markdown(
        f"""
        <div class="welcome-panel" style="min-height:110px">
            <div class="welcome-label">{tr('step1_label')}</div>
            <h2>{tr('contact_info')}</h2>
            <p>{tr('contact_desc')}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(0.5, text=tr("progress1"))

    draft = st.session_state.customer_details_draft
    with st.form("customer_details_step", clear_on_submit=False):
        customer_type_options = [tr("new"), tr("existing")]
        saved_type = draft.get("customer_type", "New")
        selected_type_index = 0 if saved_type == "New" else 1
        customer_type_display = st.radio(
            tr("customer_type"),
            customer_type_options,
            horizontal=True,
            index=selected_type_index,
        )
        customer_type = "New" if customer_type_display == tr("new") else "Existing"

        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input(
                tr("full_name"),
                value=draft.get("customer_name", ""),
                placeholder=tr("name_placeholder"),
            )
            email = st.text_input(
                tr("email"),
                value=draft.get("email", ""),
                placeholder=tr("email_placeholder"),
            )
            phone = st.text_input(
                tr("phone"),
                value=draft.get("phone", ""),
                placeholder=tr("phone_placeholder"),
                help=tr("phone_help"),
            )
        with col2:
            client_id = st.text_input(
                tr("client_id"),
                value=draft.get("client_id", ""),
                placeholder=tr("client_placeholder"),
                help=tr("client_help"),
            )
            order_id = st.text_input(
                tr("order_id"),
                value=draft.get("order_id", ""),
                placeholder=tr("order_placeholder"),
            )

        continue_clicked = st.form_submit_button(
            tr("continue"), type="primary", use_container_width=True
        )

    if continue_clicked:
        if not customer_name.strip():
            st.error(tr("name_error"))
        elif not email_is_valid(email):
            st.error(tr("email_error"))
        elif not phone_is_valid(phone):
            st.error(tr("phone_error"))
        elif customer_type == "Existing" and not client_id.strip():
            st.error(tr("client_error"))
        else:
            st.session_state.customer_details_draft = {
                "customer_type": customer_type,
                "client_id": client_id.strip(),
                "customer_name": customer_name.strip(),
                "email": email.strip(),
                "phone": phone.strip(),
                "order_id": order_id.strip(),
            }
            st.session_state.page = "New Complaint — Step 2"
            st.rerun()


# =========================================================
# NEW COMPLAINT — STEP 2
# =========================================================
elif st.session_state.page == "New Complaint — Step 2":
    page_heading(tr("step1_heading"), tr("step2_subtitle"), "✚")
    st.progress(1.0, text=tr("progress2"))

    customer = st.session_state.customer_details_draft
    with st.container(border=True):
        st.markdown(f"#### {tr('customer_details')}")
        detail_cols = st.columns(3)
        detail_cols[0].write(f"**{tr('name')}**  \n{safe_value(customer.get('customer_name'))}")
        detail_cols[1].write(f"**{tr('email')}**  \n{safe_value(customer.get('email'))}")
        detail_cols[2].write(f"**{tr('customer_type')}**  \n{tr('new') if customer.get('customer_type') == 'New' else tr('existing')}")
        if customer.get("order_id"):
            st.caption(f"{tr('order_id')}: {customer['order_id']}")

    categories = [
        "Shipping", "Returns", "Refunds", "Products",
        "Technical Support", "Billing", "Account", "Warranty", "Other",
    ]
    display_to_internal = {tr(CATEGORY_KEYS[item]): item for item in categories}
    display_categories = [tr(CATEGORY_KEYS[item]) for item in categories]
    saved_category = st.session_state.complaint_category_draft
    saved_display_category = tr(CATEGORY_KEYS[saved_category]) if saved_category in CATEGORY_KEYS else None

    with st.form("complaint_details_step", clear_on_submit=False):
        category_display = st.selectbox(
            tr("category"),
            [""] + display_categories,
            index=(display_categories.index(saved_display_category) + 1)
            if saved_display_category in display_categories else 0,
            format_func=lambda value: tr("select_category") if value == "" else value,
        )
        complaint = st.text_area(
            tr("describe_issue"),
            value=st.session_state.complaint_text_draft,
            placeholder=tr("complaint_placeholder"),
            height=180,
            max_chars=4000,
        )
        back_col, submit_col = st.columns([1, 2])
        with back_col:
            back_clicked = st.form_submit_button(tr("back"), use_container_width=True)
        with submit_col:
            submit_clicked = st.form_submit_button(
                tr("submit"), type="primary", use_container_width=True
            )

    if back_clicked:
        st.session_state.complaint_category_draft = display_to_internal.get(category_display, "")
        st.session_state.complaint_text_draft = complaint
        st.session_state.page = "New Complaint — Step 1"
        st.rerun()

    if submit_clicked:
        if not category_display:
            st.error(tr("category_error"))
        elif not complaint.strip():
            st.error(tr("complaint_error"))
        else:
            category = display_to_internal[category_display]
            st.session_state.complaint_category_draft = category
            st.session_state.complaint_text_draft = complaint
            full_query = (
                f"Customer-selected category: {category}\n"
                f"Customer complaint: {complaint.strip()}"
            )
            try:
                with st.spinner(tr("processing")):
                    result = asyncio.run(process_customer_query(full_query, customer))
                st.session_state.latest_result = result
                st.session_state.page = "Latest Result"
                st.session_state.customer_details_draft = {}
                st.session_state.complaint_category_draft = ""
                st.session_state.complaint_text_draft = ""
                st.rerun()
            except Exception as error:
                st.error(tr("processing_error"))
                st.exception(error)


# =========================================================
# LATEST RESULT
# =========================================================
elif st.session_state.page == "Latest Result":
    result = st.session_state.latest_result
    if result:
        render_latest_result(result)
    else:
        st.info(tr("no_history"))
        if st.button(tr("go_overview")):
            navigate("Overview")


# =========================================================
# TICKET HISTORY
# =========================================================
elif st.session_state.page == "Ticket History":
    page_heading(tr("history_title"), tr("history_subtitle"), "▤")
    tickets = load_tickets()
    if tickets.empty:
        st.info(tr("no_history"))
    else:
        search = st.text_input(
            tr("search_tickets"),
            placeholder=tr("search_placeholder"),
        )
        filtered = tickets.copy()
        if search.strip():
            mask = filtered.astype(str).apply(
                lambda column: column.str.contains(search, case=False, na=False)
            ).any(axis=1)
            filtered = filtered[mask]
        st.caption(f"{len(filtered)} {tr('tickets_found')}")
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        st.download_button(
            tr("download_history"),
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="technohexagone_ticket_history.csv",
            mime="text/csv",
        )


# =========================================================
# KNOWLEDGE BASE
# =========================================================
elif st.session_state.page == "Knowledge Base":
    page_heading(tr("kb_page_title"), tr("kb_page_subtitle"), "📚")
    documents = sorted(KB_DIR.glob("*.md")) if KB_DIR.exists() else []
    if not documents:
        st.warning(tr("no_docs"))
    else:
        st.metric(tr("available_docs"), len(documents))
        selected_document = st.selectbox(
            tr("select_doc"),
            documents,
            format_func=lambda path: path.name,
        )
        if selected_document:
            st.markdown(
                f'<div class="document-card"><h3>{html.escape(selected_document.name)}</h3></div>',
                unsafe_allow_html=True,
            )
            # The source documents are kept in their original language/content.
            st.markdown(selected_document.read_text(encoding="utf-8"))


# =========================================================
# ABOUT
# =========================================================
elif st.session_state.page == "About":
    page_heading(tr("about_title"), tr("about_subtitle"), "ⓘ")
    show_image("support_banner.png", use_container_width=True)
    st.write(tr("about_text"))
    st.markdown(f"### {tr('our_agents')}")
    for title, description in [
        (f"01 · {tr('query_agent')}", tr("query_about")),
        (f"02 · {tr('kb_agent')}", tr("kb_about")),
        (f"03 · {tr('resolution_agent')}", tr("resolution_about")),
        (f"04 · {tr('log_agent')}", tr("log_about")),
    ]:
        with st.expander(title):
            st.write(description)
    st.markdown(f"### {tr('technology')}")
    st.write(tr("technology_list"))
