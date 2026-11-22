"""
REP-TC082: Workflow Activity Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/wf_settings_activity/
2. Search by "Project", "App Number", "User" & "Status"
Expected: Only searched data should be shown
"""
import common as c

TEST_CASE_ID = "REP-TC082"
ROUTE = "/workflow/workflow_report/wf_settings_activity/"
SEARCH_LABELS = ["User", "Operation", "Source IP"]


def test_search_workflow_activity_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_report(ROUTE)
    return session.search_or_filter(SEARCH_LABELS, report_key="workflow_activity")


if __name__ == "__main__":
    c.run_report_test(
        TEST_CASE_ID, ROUTE, test_search_workflow_activity_report, __doc__
    )