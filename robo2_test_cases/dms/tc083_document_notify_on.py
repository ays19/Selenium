"""
DMS-TC083
Document Notify On
1. Go to https://ecmv6.robo2mation.com/dms/document/root
2. Select a doc-type
3. Click on "Notify On" button
4. Select one or  multiple groups in "Owner Groups" field
5. Click on "Save" button
1. Selected Owner group members should get system notification when document (including version document) is downloaded by any of the access group or owner group users.
"""
import common as c

TEST_CASE_ID = "DMS-TC083"


def notify_on(session: c.DmsSession) -> tuple[bool, str]:
    name = session.categorization.new_doc_type()
    ok, message = session.categorization.toggle_notify(name, "on")
    is_on = session.categorization.is_notify_on(name)
    passed = bool(ok) and is_on
    return passed, f"{message} ({name}). Notify is {'on' if is_on else 'OFF'}"


SCENARIOS = [("Notify on", notify_on)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
