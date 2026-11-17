"""
REP-TC013: Core API Report
1. Go to https://ecmv6.robo2mation.com/report/published-api-report/
2. Users without "Core Report Manager" permission
Expected: User should not be able to access Core > API report page
"""
import common as c

TEST_CASE_ID = "REP-TC013"
ROUTE = "/report/published-api-report/"


def test_denied_core_api_report(session: c.ReportSession) -> str:
    session.login_as_role("core_user")
    session.open_report(ROUTE, check_accessible=False)
    return session.verify_scope("denied")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_denied_core_api_report, __doc__)