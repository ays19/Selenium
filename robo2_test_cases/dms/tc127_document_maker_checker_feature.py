"""
DMS-TC127
Document Maker-Checker feature
Document Review (Upload Document for review- Maker)
1. Go to https://ecmv6.robo2mation.com/dms/document/upload/standard_upload/
2. Select a checker group assigned document type
3. Select checker and fill the necessary fields
4. Upload Document
Document should be uploaded and should go to the checker.
If checker approves the document only then it should appear on the system search and in My Documents

Roles: maker = second user (OTHER_USERNAME), checker = main user (USERNAME, 'sharar').
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC127"


def maker_checker(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = os.getenv("CHECKER_DOC_TYPE", "").strip()

    def _maker_uploads():
        info = session.upload_document("pdf", doc_type=doc_type, require_checker=True)
        hidden = not session.explorer.search_finds(info["name"], tries=2)
        return info, hidden

    info, hidden_before = session.as_other_user(_maker_uploads)
    name = info["name"]

    ok, message = session.review.review_document(name, "approve")
    if not ok:
        return False, (
            f"Checker could not approve the document ({message}). Doc type used: '{info['doc_type']}'. "
            f"Document hidden from search before approval: {'yes' if hidden_before else 'NO (it did not go to review)'}"
        )

    found_after = session.explorer.search_finds(name, tries=5)
    ok = hidden_before and found_after
    return ok, (
        f"Before approval the document is hidden in search: {'yes' if hidden_before else 'NO'}. "
        f"Checker approved it ({message}). After approval it is found in search: {'yes' if found_after else 'NO'}"
    )


SCENARIOS = [("Maker uploads, checker approves", maker_checker)]


def main() -> None:
    c.run_dms_test(
        TEST_CASE_ID,
        SCENARIOS,
        doc=__doc__,
        need_other_user=True,
        required_env=[
            ("CHECKER_DOC_TYPE", "(search text of a doc-type that has a checker group, the main user is the checker)")
        ],
    )


if __name__ == "__main__":
    main()
