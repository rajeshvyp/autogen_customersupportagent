# TechnoHexagone Store — Enterprise Knowledge Base Dataset

This is a fictional training dataset for the AI Customer Support Automation assignment.

## Contents
- 35 Markdown documents across company, shipping, returns, product catalogues, warranty, troubleshooting, billing, account security, FAQs, historical cases and escalation.
- All company names, product names, policies, and case records are fictional.
- Policies are internally consistent training examples, not legal advice or real commercial terms.

## Suggested RAG metadata
For each chunk, retain:
- 'source_file'
- 'category'
- 'section_heading'
- 'document_version'

## Retrieval guidance
Start with the assignment's simple keyword search. Later, optionally add embeddings and FAISS. Always return the source filename with retrieved passages. If no relevant evidence is found, the Resolution Agent should say so rather than inventing a policy.
