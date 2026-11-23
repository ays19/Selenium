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
    if len(first["values"]) < 2 or len(second["values"]) < 2:
        raise c.SetupError(f"Doc type '{first['doc_type']}' needs >= 2 text metadata fields (got {first['values']})")

    pos_name = session.explorer.build_cross_search_criteria(first, first)
    session.explorer.open()
    session.explorer.advanced_search(
        None, match_all=True, doc_type=first["doc_type"], extra=first["values"][:2]
    )
    pos_hits = session.explorer.find_in_search_result_pages([first["name"], second["name"]])
    pos_ok = first["name"] in pos_hits and second["name"] not in pos_hits

    _, neg_pairs = session.explorer.build_cross_search_criteria(first, second)
    session.explorer.open()
    session.explorer.advanced_search(
        None, match_all=True, doc_type=first["doc_type"], extra=neg_pairs
    )
    neg_hits = session.explorer.find_in_search_result_pages([first["name"], second["name"]])
    neg_ok = not neg_hits

    ok = pos_ok and neg_ok
    return ok, (
        f"Match All positive ({first['name']} only): {list(pos_hits)}. "
        f"Match All negative cross-values (none expected): {list(neg_hits)}"
    )


SCENARIOS = [("Match All enabled", advanced)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
