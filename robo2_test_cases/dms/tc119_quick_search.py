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
    if not (found and count == 1):
        return False, f"Search by document name '{name}' expected 1 result, got found={found}, count={count}"
    if not info["values"]:
        raise c.SetupError(f"Doc type '{info['doc_type']}' has no text meta-data to test Quick Search by metadata")

    value = info["values"][0][1]
    found_meta, count_meta = session.explorer.quick_search_for(value, name)
    passed = found_meta and count_meta == 1
    return passed, (
        f"Search by name '{name}' shows 1 result. Search by meta-data '{value}' -> "
        f"found={'yes' if found_meta else 'NO'} ({count_meta} result(s))"
    )


SCENARIOS = [("Quick search", quick_search)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
