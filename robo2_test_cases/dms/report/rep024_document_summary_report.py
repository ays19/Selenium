"""
REP-TC024: Document Summary Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/document_summary/
Expected:
1. Admin or permitted user should see all users document summary report
2. General users should see their own document summary report
"""
import common as c

TEST_CASE_ID = "REP-TC024"
ROUTE = "/dms/dms_report/document_summary/"


def test_document_summary_report(session: c.ReportSession) -> str:
    # Document Summary renders a Chart.js <canvas> (no HTML table rows to text-match),
    # so verify chart accessibility for both roles and the manager's "All Users" scope.
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    manager_msg = session.verify_scope("accessible")
    if "all users" not in session.report_page.body_text().casefold():
        raise AssertionError("Expected 'All Users' selector on manager's Document Summary Report.")

    session.login_as_role("dms_user")
    session.open_report(ROUTE)
    user_msg = session.verify_scope("accessible")

    return f"{manager_msg} ('All Users' visible) | {user_msg}"


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_document_summary_report, __doc__)