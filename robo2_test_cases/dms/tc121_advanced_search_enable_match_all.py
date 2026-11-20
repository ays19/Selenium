"""
DMS-TC121
Advanced Search (Enable Match All)
1. Click on global search arrow icon
2. Select doc type
3. Give metadata
4. Enable "Match All"
5. Click on "Search"
System should only show only those documents which matched all meta field data
"""
import common as c

TEST_CASE_ID = "DMS-TC121"


def advanced(session: c.DmsSession) -> tuple[bool, str]:
    first = session.upload_document("pdf")
    second = session.upload_document("pdf")
    name, pairs = session.explorer.build_cross_search_criteria(first, second)

    session.explorer.open()
    session.explorer.advanced_search(name, match_all=True, doc_type=first["doc_type"], extra=pairs)
    text = session.explorer.body_text()
    found_a = first["name"].lower() in text
    found_b = second["name"].lower() in text
    ok = not found_a and not found_b
    return ok, (
        f"Match All on: first document {'shown' if found_a else 'not shown'}, "
        f"second document {'shown' if found_b else 'not shown'} (expected neither document)"
    )


SCENARIOS = [("Match All enabled", advanced)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
