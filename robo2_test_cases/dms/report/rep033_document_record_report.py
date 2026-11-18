"""
REP-TC033: Document Record Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/document-record-report/
2. Search by Uploader, Document Name, Document Type or Metafield
Expected: Search by Uploader, Document Name, Document Type or Metafield should display related data
"""
import common as c

TEST_CASE_ID = "REP-TC033"
ROUTE = "/dms/dms_report/document-record-report/"
SEARCH_LABELS = ["Uploader"]


def test_search_document_record_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    session.select_document_type()
    return session.search_or_filter(
        SEARCH_LABELS,
        expected_key="REPORT_EXPECTED_FILTER_TEXT_DOCUMENT_RECORD_REPORT",
    )


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_search_document_record_report, __doc__)
