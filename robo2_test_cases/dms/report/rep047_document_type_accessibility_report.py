"""
REP-TC047: Document Type (Accessibility) Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/document-type-report/
2. Filter By Users
Expected: Filtered data should be accessible
"""
import common as c

TEST_CASE_ID = "REP-TC047"
ROUTE = "/dms/dms_report/document-type-report/"


def test_filter_document_type_accessibility_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    return session.filter_by_user()


if __name__ == "__main__":
    c.run_report_test(
        TEST_CASE_ID, ROUTE, test_filter_document_type_accessibility_report, __doc__
    )
