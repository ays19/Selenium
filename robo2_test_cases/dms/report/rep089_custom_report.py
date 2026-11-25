"""
REP-TC089: Custom Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/general_report
2. User's only with "All Process Information"
Expected: Should see all users activity report of all processes
"""
import common as c

TEST_CASE_ID = "REP-TC089"
ROUTE = "/workflow/workflow_report/general_report"
REPORT_NAME = "Default Variable Report"


def test_all_process_custom_report(session: c.ReportSession) -> str:
    username = session.login_as_role("wf_admin")
    session.open_custom_report(ROUTE, report_name=REPORT_NAME)
    return session.verify_other_user_visible(username)


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_all_process_custom_report, __doc__)