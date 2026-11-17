"""
REP-TC005: Export/Print/Copy Login Report
1. Go to https://ecmv6.robo2mation.com/report/login_report/
2. Click on "Copy", "CSV" or "Print" button
Expected: Selected rows login report should be copied, printed or (csv) downloaded respectively
"""
import common as c

TEST_CASE_ID = "REP-TC005"
ROUTE = "/report/login_report/"


def test_export_login_report(session: c.ReportSession) -> str:
    session.login_as_role("core_report_manager")
    session.open_report(ROUTE)
    return session.export(["Copy", "CSV"])


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_export_login_report, __doc__)