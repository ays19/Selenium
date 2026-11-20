"""
DMS-TC077
Deleted Category Permanent Deletion
1. Go to https://ecmv6.robo2mation.com/dms/document/deleted-root
2. Select a category/doc-type
3. Click on "Delete Permanently"
4. Click on "Yes" on confirmation modal
Selected category/doc-type should be permanently deleted
"""
import common as c

TEST_CASE_ID = "DMS-TC077"


def delete_permanently(session: c.DmsSession) -> tuple[bool, str]:
    name = session.categorization.new_doc_type()
    ok, message = session.categorization.delete_category(name)
    if not ok:
        raise c.SetupError(f"could not delete the doc-type ({message})")

    return session.categorization.permanently_delete_category(name)


SCENARIOS = [("Delete permanently", delete_permanently)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
