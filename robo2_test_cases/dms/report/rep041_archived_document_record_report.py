"""
REP-TC041: Archived Document Record Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/archived-document-report/
2. Filter By Document Type
Expected: Filtered data should be accessible
"""
import common as c

TEST_CASE_ID = "REP-TC041"
ROUTE = "/dms/dms_report/archived-document-report/"


def test_filter_archived_document_record_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    doc_type = session.select_document_type()
    session.report_page.assert_table_contains(doc_type, "Document Type filtered result")
    return f"Filtered by Document Type '{doc_type}' and verified matching rows."


if __name__ == "__main__":
    c.run_report_test(
        TEST_CASE_ID, ROUTE, test_filter_archived_document_record_report, __doc__
    )
