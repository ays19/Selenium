"""
DMS-TC139
Chat with PDF
1. Upload a pdf file
2. Go to document details/full view page
3. Ask something
AI should provide proper response
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC139"
QUESTION = "What is this document about?"


def chat(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = os.getenv("OCR_DOC_TYPE", "/1 FC Test updated/OCR Test/")
    info = session.upload_document("pdf", doc_type=doc_type)
    session.explorer.open_document(info["name"])
    return session.document.ask_effy_chat(QUESTION, timeout_seconds=60)


SCENARIOS = [("Chat with PDF", chat)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
