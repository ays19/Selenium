"""
REP-TC097: Auto Approval Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/wf_auto_approval/
2. User's only with "All Process Information"
3. Assigned in no task
Expected: Should see all users auto approved report of all processes
"""
import common as c

TEST_CASE_ID = "REP-TC097"
ROUTE = "/workflow/workflow_report/wf_auto_approval/"


def test_all_process_auto_approval_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_report(ROUTE)
    return session.verify_scope("all")


if __name__ == "__main__":
    c.run_report_test(
        TEST_CASE_ID, ROUTE, test_all_process_auto_approval_report, __doc__
    )