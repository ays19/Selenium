"""
DMS-TC136
PDF Document OCR from Advanced Search
1. Enable OCR for a document type
2. Upload readable quality pdf document
3. Wait until OCR status is done
4. In Advanced search Select OCR enabled document type
5. Type document content in "Content Search" field
6. Observe the results
Matched content should show the respective document
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC136"


def ocr_advanced_search(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = os.getenv("OCR_DOC_TYPE", "").strip()
    search_text = os.getenv("OCR_SEARCH_TEXT", "").strip()

    info = session.upload_document("pdf", doc_type=doc_type)
    name = info["name"]
    ok, status_msg = session.open_and_wait_for_ocr(name, timeout_seconds=60)
    if not ok:
        return False, f"{status_msg} for document '{name}'"

    session.explorer.open()
    session.explorer.advanced_search(
        None, match_all=True, doc_type=info["doc_type"], extra=[("content search", search_text)]
    )
    pos_found = bool(session.explorer.find_in_search_result_pages([name], max_pages=5))

    neg_query = "ZZZ_NO_MATCH_99999"
    session.explorer.open()
    session.explorer.advanced_search(
        None, match_all=True, doc_type=info["doc_type"], extra=[("content search", neg_query)]
    )
    neg_found = bool(session.explorer.find_in_search_result_pages([name], max_pages=3))

    passed = pos_found and not neg_found
    return passed, (
        f"Content search '{search_text}' found='{pos_found}', negative '{neg_query}' found='{neg_found}' ({status_msg})"
    )


SCENARIOS = [("OCR advanced search", ocr_advanced_search)]


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
