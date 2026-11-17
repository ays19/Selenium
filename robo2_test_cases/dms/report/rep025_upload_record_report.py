"""
REP-TC025: Upload Record Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/upload_report/
2. Users without "DMS Report Manager" permission
Expected: User should be able to access only their uploaded documents
"""
import common as c

TEST_CASE_ID = "REP-TC025"
ROUTE = "/dms/dms_report/upload_report/"


def test_own_upload_record_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_user")
    session.open_report(ROUTE)
    session.select_document_type()
    return session.verify_scope("own")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_own_upload_record_report, __doc__)