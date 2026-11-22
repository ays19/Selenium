"""
REP-TC091: Custom Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/general_report
2. Select a date range
Expected: Only selected dates data should be shown
"""
import common as c

TEST_CASE_ID = "REP-TC091"
ROUTE = "/workflow/workflow_report/general_report"
REPORT_NAME = "Test Report 1"


def test_date_range_custom_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_custom_report(ROUTE, report_name=REPORT_NAME)
    return session.filter_by_date()


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_date_range_custom_report, __doc__)