"""
DMS-TC125
Save Search
1. Click on global search arrow icon
2. Select doc type
3. Give metadata
4. Click on "Save Search"
5. Give a search name & click on "Save"
An advanced search result should be saved
"""
from datetime import datetime

import common as c

TEST_CASE_ID = "DMS-TC125"


def saving(session: c.DmsSession) -> tuple[bool, str]:
    info = session.upload_document()
    search_name = datetime.now().strftime("AUTO_SEARCH_%H%M%S")
    ok, message = session.explorer.save_search(search_name, info)
    return ok, f"{message} ({search_name})"


SCENARIOS = [("Save search", saving)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
