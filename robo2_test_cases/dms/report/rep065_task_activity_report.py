"""
REP-TC065: Task Activity Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/wf_activity
2. User's only with "Related Process Information"
3. Assigned in any task as user/group user
Expected: Should see all users activity report of that assigned process
"""
import common as c

TEST_CASE_ID = "REP-TC065"
ROUTE = "/workflow/workflow_report/wf_activity"


def test_related_process_task_activity_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_related_process_user")
    session.open_report(ROUTE)
    return session.verify_scope("all")


if __name__ == "__main__":
    c.run_report_test(
        TEST_CASE_ID, ROUTE, test_related_process_task_activity_report, __doc__
    )