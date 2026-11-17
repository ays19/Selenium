"""
REP-TC020: DMS Activity Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/dms_activity/
2. Search by "User", "Operation" or "Source IP"
Expected: Only searched data should be shown
"""
import common as c

TEST_CASE_ID = "REP-TC020"
ROUTE = "/dms/dms_report/dms_activity/"
SEARCH_LABELS = ["User", "Operation", "Source IP"]


def test_search_dms_activity_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    return session.search_or_filter(
        SEARCH_LABELS,
        expected_key="REPORT_EXPECTED_FILTER_TEXT_DMS_ACTIVITY_REPORT",
    )


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_search_dms_activity_report, __doc__)