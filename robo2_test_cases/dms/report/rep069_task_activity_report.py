"""
REP-TC069: Task Activity Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/wf_activity
2. Filter by user
Expected: Selected users task activity report should be shown
"""
import common as c

TEST_CASE_ID = "REP-TC069"
ROUTE = "/workflow/workflow_report/wf_activity"
FILTER_LABELS = ["User"]


def test_filter_task_activity_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_report(ROUTE)
    return session.search_or_filter(FILTER_LABELS, report_key="task_activity")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_filter_task_activity_report, __doc__)
