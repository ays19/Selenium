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
    checker_name = os.getenv("CHECKER_NAME", "").strip() or None
    app_info = session.upload_document("pdf", doc_type=doc_type, require_checker=True, checker_name=checker_name)
    rej_info = session.upload_document("pdf", doc_type=doc_type, require_checker=True, checker_name=checker_name)
    approved, rejected = app_info["name"], rej_info["name"]

    ok_a, msg_a = session.review_as_checker(approved, "approve")
    ok_r, msg_r = session.review_as_checker(rejected, "reject")

    approved_search = session.explorer.search_finds(approved, tries=5)
    approved_explorer = session.explorer.explorer_has(app_info["doc_type"], approved)
    approved_review_tab = session.review.is_listed_in_requested_by_me("Approved", approved)

    rejected_search = session.explorer.search_finds(rejected)
    rejected_explorer = session.explorer.explorer_has(rej_info["doc_type"], rejected)
    rejected_review_tab = session.review.is_listed_in_requested_by_me("Rejected", rejected)

    ok = (
        ok_a
        and ok_r
        and approved_search
        and approved_explorer
        and approved_review_tab
        and not rejected_search
        and not rejected_explorer
        and rejected_review_tab
    )
    return ok, (
        f"Approve: {msg_a} (Search={approved_search}, Explorer={approved_explorer}, ReviewApproved={approved_review_tab}). "
        f"Reject: {msg_r} (Search={rejected_search}, Explorer={rejected_explorer}, ReviewRejected={rejected_review_tab})"
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
