"""
REP-TC096: Auto Approval Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/wf_auto_approval/
2. User's only with "Related Process Information"
3. Assigned in any task as user/group user
Expected: Should see all users auto approved report of that assigned process
"""
import common as c

TEST_CASE_ID = "REP-TC096"
ROUTE = "/workflow/workflow_report/wf_auto_approval/"


def test_related_process_auto_approval_report(session: c.ReportSession) -> str:
    username = session.login_as_role("wf_related_process_user")
    session.open_report(ROUTE)
    return session.verify_other_user_visible(username)


if __name__ == "__main__":
    c.run_report_test(
        TEST_CASE_ID, ROUTE, test_related_process_auto_approval_report, __doc__
    )