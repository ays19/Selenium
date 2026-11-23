"""
DMS-TC137
PDF Document OCR from My Documents Search
1. Enable OCR for a document type
2. Upload readable quality pdf document
3. Wait until OCR status is done
4. In Explorer search Select OCR enabled document type
5. Type document content in "Content Search" field
6. Observe the results
Matched content should show the respective document
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC137"


def ocr_explorer_search(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = os.getenv("OCR_DOC_TYPE", "").strip()
    search_text = os.getenv("OCR_SEARCH_TEXT", "").strip()

    info = session.upload_document("pdf", doc_type=doc_type)
    name = info["name"]
    ok, status_msg = session.open_and_wait_for_ocr(name, timeout_seconds=60)
    if not ok:
        return False, f"{status_msg} for document '{name}'"

    pos_found, pos_rows = session.explorer.explorer_content_search(info["doc_type"], search_text, name)
    neg_query = "ZZZ_NO_MATCH_99999"
    neg_found, _ = session.explorer.explorer_content_search(info["doc_type"], neg_query, name)

    passed = pos_found and not neg_found
    return passed, (
        f"Explorer content search '{search_text}' found='{pos_found}' ({len(pos_rows)} row(s)), "
        f"negative '{neg_query}' found='{neg_found}' ({status_msg})"
    )


SCENARIOS = [("OCR My Documents search", ocr_explorer_search)]


def main() -> None:
    c.run_dms_test(
        TEST_CASE_ID,
        SCENARIOS,
        doc=__doc__,
        required_env=[
            ("OCR_DOC_TYPE", "(search text of a doc-type with OCR enabled)"),
            ("OCR_SEARCH_TEXT", "(a word that is inside the sample pdf)"),
        ],
    )


if __name__ == "__main__":
    main()
