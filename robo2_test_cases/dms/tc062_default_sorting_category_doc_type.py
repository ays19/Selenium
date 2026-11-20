"""
DMS-TC062
Default Sorting on My Docments Category/Doc-Type
1. Go to https://ecmv6.robo2mation.com/dms/document/explorer/
By default category/doc-type should be shown as name wise ascending
"""
import common as c

TEST_CASE_ID = "DMS-TC062"


def category_sorting(session: c.DmsSession) -> tuple[bool, str]:
    return session.explorer.verify_tree_default_sorting()


SCENARIOS = [("Default category sorting", category_sorting)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
