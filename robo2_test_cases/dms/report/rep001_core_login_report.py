"""
REP-TC001: Core Login Report
1. Go to https://ecmv6.robo2mation.com/report/login_report/
2. Users without "Core Report Manager" permission
Expected: Should see his/her own "Login" report
"""
import common as c

TEST_CASE_ID = "REP-TC001"
ROUTE = "/report/login_report/"


def test_own_login_report(session: c.ReportSession) -> str:
    session.login_as_role("core_user")
    session.open_report(ROUTE)
    return session.verify_scope("own")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_own_login_report, __doc__)