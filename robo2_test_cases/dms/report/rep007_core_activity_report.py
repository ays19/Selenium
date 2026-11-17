"""
REP-TC007: Core Activity Report
1. Go to https://ecmv6.robo2mation.com/report/activity-report/
2. Users with "Core Report Manager" permission
Expected: Should see all users "Core Activity" report
"""
import common as c

TEST_CASE_ID = "REP-TC007"
ROUTE = "/report/activity-report/"


def test_all_users_core_activity_report(session: c.ReportSession) -> str:
    session.login_as_role("core_report_manager")
    session.open_report(ROUTE)
    return session.verify_scope("all")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_all_users_core_activity_report, __doc__)