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
    checker_name = os.getenv("CHECKER_NAME", "").strip() or None

    def _maker_uploads():
        info = session.upload_document(
            "pdf", doc_type=doc_type, require_checker=True, checker_name=checker_name
        )
        hidden_search = not session.explorer.search_finds(info["name"], tries=2)
        hidden_explorer = not session.explorer.explorer_has(info["doc_type"], info["name"])
        return info, (hidden_search and hidden_explorer)

    info, hidden_before = session.as_other_user(_maker_uploads)
    name = info["name"]

    ok, message = session.review.review_document(name, "approve")
    if not ok:
        return False, (
            f"Checker could not approve '{name}' ({message}). Doc type: '{info['doc_type']}'. "
            f"Hidden before approval: {'yes' if hidden_before else 'NO'}"
        )

    found_search = session.explorer.search_finds(name, tries=5)
    found_explorer = session.explorer.explorer_has(info["doc_type"], name)
    ok = hidden_before and found_search and found_explorer
    return ok, (
        f"Before approval hidden in search & Explorer: {'yes' if hidden_before else 'NO'}. "
        f"Checker approved ({message}). After approval Quick Search={'yes' if found_search else 'NO'}, "
        f"Explorer={'yes' if found_explorer else 'NO'}"
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
