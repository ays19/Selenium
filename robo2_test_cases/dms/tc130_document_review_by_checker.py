"""
DMS-TC130
Document Maker-Checker feature
Document Review by checker
1. Go to https://ecmv6.robo2mation.com/dms/document/pending-for-review/
2. By default, "Requested by others" is selected
3. Check the pending document list with option for approve/reject
4. Check the pending documents by "Select maker" filter
5. Apply "Upload date range" filter and check the document list
Results should show accordingly
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC130"


def checker_list(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = os.getenv("CHECKER_DOC_TYPE", "").strip()
    info = session.upload_document("pdf", doc_type=doc_type, require_checker=True)
    name = info["name"]

    shown, approve, reject = session.as_other_user(
        lambda: session.review.has_checker_actions(name)
    )
    ok = shown and approve and reject
    return ok, (
        f"Checker sees the document: {'yes' if shown else 'NO'}, "
        f"approve option: {'yes' if approve else 'NO'}, "
        f"reject option: {'yes' if reject else 'NO'}. "
        "Maker and upload date filters are not checked by the script"
    )


SCENARIOS = [("Checker pending list", checker_list)]


def main() -> None:
    c.run_dms_test(
        TEST_CASE_ID,
        SCENARIOS,
        doc=__doc__,
        need_other_user=True,
        required_env=[
            ("CHECKER_DOC_TYPE", "(search text of a doc-type that has a checker group, the second user is the checker)")
        ],
    )


if __name__ == "__main__":
    main()
