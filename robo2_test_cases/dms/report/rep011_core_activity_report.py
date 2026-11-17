"""
REP-TC011: Core Activity Report
1. Go to https://ecmv6.robo2mation.com/report/activity-report/
2. Sort by "Users Name", "Operation", "Description" & "IP Address"
Expected: Core activity report should be sorted
"""
import common as c

TEST_CASE_ID = "REP-TC011"
ROUTE = "/report/activity-report/"
SORT_COLUMNS = ["Users Name", "Operation", "Description", "IP Address"]


def test_sort_core_activity_report(session: c.ReportSession) -> str:
    session.login_as_role("core_report_manager")
    session.open_report(ROUTE)
    return session.sort_by(SORT_COLUMNS)


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_sort_core_activity_report, __doc__)