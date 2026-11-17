"""
REP-TC006: Core Activity Report
1. Go to https://ecmv6.robo2mation.com/report/activity-report/
2. Users without "Core Report Manager" permission
Expected: Should see his/her own "Core Activity" report
"""
import common as c

TEST_CASE_ID = "REP-TC006"
ROUTE = "/report/activity-report/"


def test_own_core_activity_report(session: c.ReportSession) -> str:
    session.login_as_role("core_user")
    session.open_report(ROUTE)
    return session.verify_scope("own")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_own_core_activity_report, __doc__)