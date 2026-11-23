"""
REP-TC095: Auto Approval Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/wf_auto_approval/
2. User's without "All Process Information" & "Related Process Information"
Expected: Should see his/her auto approved tasks
"""
import common as c

TEST_CASE_ID = "REP-TC095"
ROUTE = "/workflow/workflow_report/wf_auto_approval/"


def test_own_auto_approval_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_user")
    session.open_report(ROUTE)
    return session.verify_scope("own")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_own_auto_approval_report, __doc__)