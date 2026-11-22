"""
REP-TC088: Custom Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/general_report
2. User's only with "Related Process Information"
3. Assigned in any task as user/group user
Expected: Should see all users activity report of that assigned process
"""
import common as c

TEST_CASE_ID = "REP-TC088"
ROUTE = "/workflow/workflow_report/general_report"


def test_related_process_custom_report(session: c.ReportSession) -> str:
    username = session.login_as_role("wf_related_process_user")
    session.open_custom_report(ROUTE)
    return session.verify_other_user_visible(username)


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_related_process_custom_report, __doc__)