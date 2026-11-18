"""
REP-TC048: Export Document Type (Accessibility) Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/document-type-report/
2. Click on "Download" icon
3. Click on Excel
Expected:
1. Selected rows DMS activity report should be copied, printed or (csv, excel) downloaded respectively
2. For Large dataset download link should be generated in "Requested Downloads"
"""
import common as c

TEST_CASE_ID = "REP-TC048"
ROUTE = "/dms/dms_report/document-type-report/"
EXPORT_ACTIONS = ["Copy", "CSV", "Excel"]


def test_export_document_type_accessibility_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    return session.export(EXPORT_ACTIONS, requested_download=True)


if __name__ == "__main__":
    c.run_report_test(
        TEST_CASE_ID, ROUTE, test_export_document_type_accessibility_report, __doc__
    )