"""
DMS-TC075
Deleted Category Map
1. Go to https://ecmv6.robo2mation.com/dms/document/deleted-root
2. Select a category
3. Click on "See Map"
Selected categories map will be shown
"""
from datetime import datetime

import common as c

TEST_CASE_ID = "DMS-TC075"


def see_map(session: c.DmsSession) -> tuple[bool, str]:
    name = datetime.now().strftime("AUTO_CAT_%H%M%S")
    ok, message = session.categorization.create_category(name, "category")
    if not ok:
        raise c.SetupError(f"category could not be created ({message})")

    ok, message = session.categorization.delete_category(name)
    if not ok:
        raise c.SetupError(f"could not delete the category ({message})")

    return session.categorization.see_deleted_map(name)


SCENARIOS = [("See map", see_map)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
