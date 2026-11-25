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
    checker_name = os.getenv("CHECKER_NAME", "").strip() or c.cfg.USERNAME
    info = session.upload_document("pdf", doc_type=doc_type, require_checker=True, checker_name=checker_name)
    name = info["name"]
    maker_filter_term = os.getenv("CHECKER_NAME", "").strip() or c.cfg.USERNAME

    def _verify_checker_view():
        val, default_label = session.review.default_user_filter()
        default_is_others = (val == "1") and ("others" in default_label.lower())
        shown, approve, reject = session.review.has_checker_actions(name)

        session.review.search_table("")
        session.review.select_maker_filter(maker_filter_term)
        maker_hit = session.review.table_contains(name)

        today = session.review.today_ymd()
        session.review.apply_date_range("maker-date", today, today)
        today_hit = session.review.table_contains(name)
        session.review.apply_date_range("maker-date", "2020-01-01", "2020-01-02")
        past_miss = not session.review.table_contains(name, timeout=4)
        session.review.clear_date_range("maker-date")

        return {
            "default_is_others": default_is_others,
            "default_label": default_label,
            "shown": shown,
            "approve": approve,
            "reject": reject,
            "maker_hit": maker_hit,
            "date_ok": today_hit and past_miss,
        }

    try:
        res = session.as_other_user(_verify_checker_view)
    finally:
        try:
            session.review_as_checker(name, "reject")
        except Exception:
            pass

    ok = (
        res["default_is_others"]
        and res["shown"]
        and res["approve"]
        and res["reject"]
        and res["maker_hit"]
        and res["date_ok"]
    )
    return ok, (
        f"Default filter='{res['default_label']}', listed={res['shown']}, "
        f"approve={res['approve']}, reject={res['reject']}, maker filter={res['maker_hit']}, "
        f"upload date filter={res['date_ok']}"
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
