"""
REP-TC009: Core Activity Report
1. Go to https://ecmv6.robo2mation.com/report/activity-report/
2. Search by "Users Name" & "Operations"
Expected: Only searched data should be shown
"""
import common as c

TEST_CASE_ID = "REP-TC009"
ROUTE = "/report/activity-report/"
SEARCH_LABELS = ["Users Name", "Operations"]


def test_search_core_activity_report(session: c.ReportSession) -> str:
    session.login_as_role("core_report_manager")
    session.open_report(ROUTE)
    return session.search_or_filter(SEARCH_LABELS, report_key="core_activity")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_search_core_activity_report, __doc__)
