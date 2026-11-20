"""
REP-TC015: Core API Report
1. Go to https://ecmv6.robo2mation.com/report/published-api-report/
2. Search by REQUEST URL, IP, METHOD, STATUS CODE
Expected: Only searched data should be shown
"""
import common as c

TEST_CASE_ID = "REP-TC015"
ROUTE = "/report/published-api-report/"
SEARCH_LABELS = ["REQUEST URL", "IP", "METHOD", "STATUS CODE"]


def test_search_core_api_report(session: c.ReportSession) -> str:
    session.login_as_role("core_report_manager")
    session.open_report(ROUTE)
    return session.search_or_filter(SEARCH_LABELS, report_key="core_api")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_search_core_api_report, __doc__)
