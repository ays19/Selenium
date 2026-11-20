"""
DMS-TC126
Save Search
1. Go to save search list
2. Double click on a save search
3. Click on "Search"
Saved search list should be shown & by double clicking on a saved search should fillup relavent metadata
"""
from datetime import datetime

import common as c

TEST_CASE_ID = "DMS-TC126"


def saved_search_list(session: c.DmsSession) -> tuple[bool, str]:
    info = session.upload_document()
    search_name = datetime.now().strftime("AUTO_SEARCH_%H%M%S")
    ok, message = session.explorer.save_search(search_name, info)
    if not ok:
        raise c.SetupError(f"could not save the search ({message})")

    return session.explorer.load_saved_search_and_verify(search_name, info)


SCENARIOS = [("Saved search list", saved_search_list)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
