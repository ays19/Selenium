"""
REP-TC027: Upload Record Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/upload_report/
2. Search by Uploader, Document Name, Document Type or Metafield
Expected: Search by Uploader, Document Name, Document Type or Metafield should display related data
"""
import common as c

TEST_CASE_ID = "REP-TC027"
ROUTE = "/dms/dms_report/upload_report/"
SEARCH_LABELS = ["Uploader", "Document Name", "Document Type", "Metafield"]


def test_search_upload_record_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    session.select_document_type()
    return session.search_or_filter(SEARCH_LABELS, report_key="upload_record")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_search_upload_record_report, __doc__)
