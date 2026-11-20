"""
DMS-TC078
Deleted Category Full Path
1. Go to https://ecmv6.robo2mation.com/dms/document/deleted-root
Categories/Doc-type full path should be shown
"""
import common as c

TEST_CASE_ID = "DMS-TC078"


def full_path(session: c.DmsSession) -> tuple[bool, str]:
    name = session.categorization.new_doc_type()
    ok, message = session.categorization.delete_category(name)
    if not ok:
        raise c.SetupError(f"could not delete the doc-type ({message})")

    path = session.categorization.get_deleted_full_path(name)
    expected = session.categorization.expected_full_path(name)
    if path == expected:
        return True, f"Full path of the deleted doc-type is shown as '{path}'"
    return False, f"Full path column shows '{path}', expected '{expected}'"


SCENARIOS = [("Full path", full_path)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
