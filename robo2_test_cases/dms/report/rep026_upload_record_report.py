"""
REP-TC026: Upload Record Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/upload_report/
2. Users with "DMS Report Manager" permission
Expected: User should be able to access all users uploaded documents
"""
import common as c

TEST_CASE_ID = "REP-TC026"
ROUTE = "/dms/dms_report/upload_report/"


def test_all_users_upload_record_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    session.select_document_type()
    return session.verify_scope("all")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_all_users_upload_record_report, __doc__)