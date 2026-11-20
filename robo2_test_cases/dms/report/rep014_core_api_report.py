"""
REP-TC014: Core API Report
1. Go to https://ecmv6.robo2mation.com/report/published-api-report/
2. Users with "Core Report Manager" permission
Expected: User should be able to access Core > API report page and access all the api users log data
"""
import common as c
from report.report_data import EXPECTED_API_TEXT

TEST_CASE_ID = "REP-TC014"
ROUTE = "/report/published-api-report/"


def test_manager_core_api_report(session: c.ReportSession) -> str:
    session.login_as_role("core_report_manager")
    session.open_report(ROUTE)

    if EXPECTED_API_TEXT:
        with session.step(f"Verify API log row '{EXPECTED_API_TEXT}' is visible"):
            session.report_page.assert_table_contains(EXPECTED_API_TEXT, "API log record")
        return f"Core Report Manager accessed Core > API report page and verified '{EXPECTED_API_TEXT}'."

    return session.verify_scope("accessible")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_manager_core_api_report, __doc__)
