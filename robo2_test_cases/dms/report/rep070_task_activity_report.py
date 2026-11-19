"""
REP-TC070: Download Task Activity Report (Back End)
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/wf_activity
2. Download Task Activity Report from back end
Expected: A downloadable URL will be generated in "Requested Downloads" page & report will be downloadable from there
"""
import common as c

TEST_CASE_ID = "REP-TC070"
ROUTE = "/workflow/workflow_report/wf_activity"
EXPORT_ACTIONS = ["CSV", "Excel"]


def test_download_task_activity_backend(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_report(ROUTE)
    return session.export(EXPORT_ACTIONS, requested_download=True)


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_download_task_activity_backend, __doc__)