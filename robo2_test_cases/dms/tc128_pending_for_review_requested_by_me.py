"""
DMS-TC128
Document Maker-Checker feature
Pending For Review
1. Go to https://ecmv6.robo2mation.com/dms/document/pending-for-review/
2. Select "Requested By Me" filter
3. Filter "Pending", "Approved" & "Rejected" files and check by checker filter
4. Apply approve date range and review date range filter and check document results
5. Search by doctype and check the "Pending", "Approved" & "Rejected" documents
Results should show accordingly

Roles: maker = second user (OTHER_USERNAME), checker = main user (USERNAME, 'sharar'), same as TC127.
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC128"


def requested_by_me(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = os.getenv("CHECKER_DOC_TYPE", "").strip()

    def _maker_uploads():
        info = session.upload_document("pdf", doc_type=doc_type, require_checker=True)
        return info, session.review.requested_by_me_statuses(info["name"])

    info, before = session.as_other_user(_maker_uploads)
    name = info["name"]
    if before != [True, False, False]:
        return False, f"Before review: shown in Pending/Approved/Rejected = {before} (expected [True, False, False])"

    ok, message = session.review.review_document(name, "approve")
    if not ok:
        raise c.SetupError(f"checker could not approve the document ({message})")

    after = session.as_other_user(lambda: session.review.requested_by_me_statuses(name))
    ok = after == [False, True, False]
    return ok, (
        f"Pending / Approved / Rejected before review {before}, after approval {after}. "
        "Date range and checker filters are not checked by the script"
    )


SCENARIOS = [("Requested by me filters", requested_by_me)]


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
