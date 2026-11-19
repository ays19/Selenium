"""
REP-TC066: Task Activity Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/wf_activity
2. User's only with "All Process Information"
Expected: Should see all users activity report of all processes
"""
import common as c

TEST_CASE_ID = "REP-TC066"
ROUTE = "/workflow/workflow_report/wf_activity"


def test_all_process_task_activity_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_report(ROUTE)
    return session.verify_scope("all")


if __name__ == "__main__":
    c.run_report_test(
        TEST_CASE_ID, ROUTE, test_all_process_task_activity_report, __doc__
    )