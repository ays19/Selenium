"""
REP-TC044: Document Type (Accessibility) Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/document-type-report/
2. Users with "DMS Report Manager" permission
Expected: User should be able to access all document type records of all users
"""
import common as c

TEST_CASE_ID = "REP-TC044"
ROUTE = "/dms/dms_report/document-type-report/"


def test_all_document_type_accessibility_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    return session.verify_user_dropdown_scope("all")


if __name__ == "__main__":
    c.run_report_test(
        TEST_CASE_ID, ROUTE, test_all_document_type_accessibility_report, __doc__
    )
