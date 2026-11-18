"""
REP-TC045: Document Type (Accessibility) Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/document-type-report/
2. Search by Document Type, Access Group, Owner Group or Full Path
Expected: Search by Document Type, Access Group, Owner Group or Full Path should display related data
"""
import common as c

TEST_CASE_ID = "REP-TC045"
ROUTE = "/dms/dms_report/document-type-report/"
SEARCH_LABELS = ["Document Type", "Access Group", "Owner Group", "Full Path"]


def test_search_document_type_accessibility_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    return session.search_or_filter(
        SEARCH_LABELS,
        expected_key="REPORT_EXPECTED_FILTER_TEXT_DOCUMENT_TYPE_REPORT",
    )


if __name__ == "__main__":
    c.run_report_test(
        TEST_CASE_ID, ROUTE, test_search_document_type_accessibility_report, __doc__
    )