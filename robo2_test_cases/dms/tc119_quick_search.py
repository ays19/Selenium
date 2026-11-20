"""
DMS-TC119
Quick Search
1. Click on global search
2. Search by doc name or any metadata
Only searched result should be shown
"""
import common as c

TEST_CASE_ID = "DMS-TC119"


def quick_search(session: c.DmsSession) -> tuple[bool, str]:
    info = session.upload_document()
    name = info["name"]

    found, count = session.explorer.quick_search_for(name, name)
    if not found:
        return False, f"Search by document name '{name}' did not show the document"
    if not info["values"]:
        return True, f"Search by document name shows the document ({count} result(s)). No text meta-data to search with"

    value = info["values"][0][1]
    found_meta, count_meta = session.explorer.quick_search_for(value, name)
    return found_meta, (
        f"Search by name shows the document ({count} result(s)). Search by meta-data '{value}' "
        + (f"shows the document ({count_meta} result(s))" if found_meta else "does NOT show the document")
    )


SCENARIOS = [("Quick search", quick_search)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
