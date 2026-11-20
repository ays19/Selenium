"""
REP-TC003: Core Login Report
1. Go to https://ecmv6.robo2mation.com/report/login_report/
2. Search by "Users Name" & "IP Address"
Expected: Only searched data should be shown
"""
import common as c

TEST_CASE_ID = "REP-TC003"
ROUTE = "/report/login_report/"
SEARCH_LABELS = ["Users Name", "IP Address"]


def test_search_login_report(session: c.ReportSession) -> str:
    session.login_as_role("core_report_manager")
    session.open_report(ROUTE)
    return session.search_or_filter(SEARCH_LABELS, report_key="core_login")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_search_login_report, __doc__)
