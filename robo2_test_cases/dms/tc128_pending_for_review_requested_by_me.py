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
    checker_name = os.getenv("CHECKER_NAME", "").strip() or os.getenv("DMS_USERNAME", "")

    def _maker_uploads():
        d1 = session.upload_document("pdf", doc_type=doc_type, require_checker=True, checker_name=checker_name)
        d2 = session.upload_document("pdf", doc_type=doc_type, require_checker=True, checker_name=checker_name)
        return d1, d2, session.review.requested_by_me_statuses(d1["name"])

    d1, d2, before = session.as_other_user(_maker_uploads)
    n1, n2 = d1["name"], d2["name"]
    if before != [True, False, False]:
        return False, f"Before review: Pending/Approved/Rejected for '{n1}' = {before} (expected [True, False, False])"

    ok_a, msg_a = session.review.review_document(n1, "approve")
    ok_r, msg_r = session.review.review_document(n2, "reject")
    if not (ok_a and ok_r):
        raise c.SetupError(f"checker review failed (approve={ok_a}:{msg_a}, reject={ok_r}:{msg_r})")

    def _verify_filters():
        after_n1 = session.review.requested_by_me_statuses(n1)
        after_n2 = session.review.requested_by_me_statuses(n2)

        today = session.review.today_ymd()
        session.review.open()
        session.review.select_user_scope("Requested By Me")
        session.review.select_status("Approved")
        session.review.select_checker_filter(checker_name)
        checker_hit = session.review.table_contains(n1)

        session.review.apply_date_range("maker-date", today, today)
        upload_today_hit = session.review.table_contains(n1)
        session.review.apply_date_range("maker-date", "2020-01-01", "2020-01-02")
        upload_past_miss = not session.review.table_contains(n1, timeout=4)
        session.review.clear_date_range("maker-date")

        session.review.apply_date_range("checker-date", today, today)
        review_today_hit = session.review.table_contains(n1)
        session.review.apply_date_range("checker-date", "2020-01-01", "2020-01-02")
        review_past_miss = not session.review.table_contains(n1, timeout=4)
        session.review.clear_date_range("checker-date")

        session.review.select_doctype_filter(doc_type)
        session.review.select_status("Approved")
        dt_approved = session.review.table_contains(n1)
        session.review.select_status("Rejected")
        dt_rejected = session.review.table_contains(n2)
        session.review.select_status("Pending")
        dt_pending_absent = not session.review.table_contains(n1, timeout=4)

        return {
            "after_n1": after_n1,
            "after_n2": after_n2,
            "checker_hit": checker_hit,
            "upload_date_ok": upload_today_hit and upload_past_miss,
            "review_date_ok": review_today_hit and review_past_miss,
            "doctype_ok": dt_approved and dt_rejected and dt_pending_absent,
        }

    res = session.as_other_user(_verify_filters)
    passed = (
        res["after_n1"] == [False, True, False]
        and res["after_n2"] == [False, False, True]
        and res["checker_hit"]
        and res["upload_date_ok"]
        and res["review_date_ok"]
        and res["doctype_ok"]
    )
    return passed, (
        f"Before={before}, Approved='{res['after_n1']}', Rejected='{res['after_n2']}'; "
        f"Checker filter={res['checker_hit']}, UploadDate={res['upload_date_ok']}, "
        f"ReviewDate={res['review_date_ok']}, Doctype={res['doctype_ok']}"
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
