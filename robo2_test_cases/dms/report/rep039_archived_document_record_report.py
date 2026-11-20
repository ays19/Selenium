"""
REP-TC039: Archived Document Record Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/archived-document-report/
2. Search by Uploader, Document Name, Document Type or Metafield
Expected: Search by Uploader, Document Name, Document Type or Metafield should display related data
"""
import common as c

TEST_CASE_ID = "REP-TC039"
ROUTE = "/dms/dms_report/archived-document-report/"
SEARCH_LABELS = ["Uploader", "Document Name", "Document Type", "Metafield"]


def test_search_archived_document_record_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    session.select_document_type()
    return session.search_or_filter(SEARCH_LABELS, report_key="archived_document_record")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_search_archived_document_record_report, __doc__)
