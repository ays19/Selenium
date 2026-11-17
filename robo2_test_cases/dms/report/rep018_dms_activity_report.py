"""
REP-TC018: DMS Activity Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/dms_activity/
2. Users without "Core Report Manager" permission
Expected: Should see his/her own "DMS Activity" report
"""
import common as c

TEST_CASE_ID = "REP-TC018"
ROUTE = "/dms/dms_report/dms_activity/"


def test_own_dms_activity_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_user")
    session.open_report(ROUTE)
    return session.verify_scope("own")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_own_dms_activity_report, __doc__)