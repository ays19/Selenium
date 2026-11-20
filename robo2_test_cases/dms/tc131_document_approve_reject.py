"""
DMS-TC131
Document Maker-Checker feature
Document approve/reject
For all the pending documents,
1. Approve the document and observe the results
2. Reject the documents and observe the results
Results should show accordingly
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC131"


def approve_reject(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = os.getenv("CHECKER_DOC_TYPE", "").strip()
    approved = session.upload_document("pdf", doc_type=doc_type, require_checker=True)["name"]
    rejected = session.upload_document("pdf", doc_type=doc_type, require_checker=True)["name"]

    ok_a, msg_a = session.review_as_checker(approved, "approve")
    ok_r, msg_r = session.review_as_checker(rejected, "reject")
    approved_found = session.explorer.search_finds(approved, tries=5)
    rejected_found = session.explorer.search_finds(rejected)
    ok = ok_a and ok_r and approved_found and not rejected_found
    return ok, (
        f"Approve: {msg_a}. Reject: {msg_r}. "
        f"Approved document found in search: {'yes' if approved_found else 'NO'}. "
        f"Rejected document found in search: {'YES' if rejected_found else 'no'}"
    )


SCENARIOS = [("Approve and reject", approve_reject)]


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
