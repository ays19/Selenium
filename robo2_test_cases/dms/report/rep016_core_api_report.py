"""
REP-TC016: Core API Report
1. Go to https://ecmv6.robo2mation.com/report/published-api-report/
2. Select a date range
Expected: Only selected dates data should be shown
"""
import common as c

TEST_CASE_ID = "REP-TC016"
ROUTE = "/report/published-api-report/"


def test_date_range_core_api_report(session: c.ReportSession) -> str:
    session.login_as_role("core_report_manager")
    session.open_report(ROUTE)
    return session.filter_by_date()


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_date_range_core_api_report, __doc__)
