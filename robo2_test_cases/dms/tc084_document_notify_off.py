"""
DMS-TC084
Document Notify Off
1. Go to https://ecmv6.robo2mation.com/dms/document/root
2. Select a doc-type
3. Click on "Notify Off" button
4. Select one or  multiple groups in "Owner Groups" field
5. Click on "Save" button
1. Selected Owner group members should not get system notification when document (including version document) is downloaded by any of the access group or owner group users.
"""
import common as c

TEST_CASE_ID = "DMS-TC084"


def notify_off(session: c.DmsSession) -> tuple[bool, str]:
    name = session.categorization.new_doc_type()

    try:
        session.categorization.toggle_notify(name, "on")
    except Exception as exc:
        raise c.SetupError(f"could not turn notify on ({c.short(exc)})") from exc
    if not session.categorization.is_notify_on(name):
        raise c.SetupError("notify did not turn on")

    ok, message = session.categorization.toggle_notify(name, "off")
    off = not session.categorization.is_notify_on(name)
    passed = off and ok is not False
    return passed, (
        f"{message} ({name}). Notify is " + ("off" if off else "STILL on")
        + ". The missing notification is not checked by the script"
    )


SCENARIOS = [("Notify off", notify_off)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
