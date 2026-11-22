"""
REP-TC083: Workflow Activity Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/wf_settings_activity/
2. Filter by "Process" name
Expected: Only filtered data should be shown
"""
import common as c

TEST_CASE_ID = "REP-TC083"
ROUTE = "/workflow/workflow_report/wf_settings_activity/"
FILTER_LABELS = ["Process"]


def test_filter_workflow_activity_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_report(ROUTE)
    return session.search_or_filter(FILTER_LABELS, report_key="workflow_activity")


if __name__ == "__main__":
    c.run_report_test(
        TEST_CASE_ID, ROUTE, test_filter_workflow_activity_report, __doc__
    )