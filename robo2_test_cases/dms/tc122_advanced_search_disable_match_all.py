"""
DMS-TC122
Advanced Search (Disable Match All)
1. Click on global search arrow icon
2. Select doc type
3. Give metadata
4. Disable "Match All"
5. Click on "Search"
System should show all documents which matched any meta field data. Maximum matched data should show first
"""
import common as c

TEST_CASE_ID = "DMS-TC122"


def advanced(session: c.DmsSession) -> tuple[bool, str]:
    first = session.upload_document("pdf")
    second = session.upload_document("pdf")
    name, pairs = session.explorer.build_cross_search_criteria(first, second)

    session.explorer.open()
    session.explorer.advanced_search(name, match_all=False, doc_type=first["doc_type"], extra=pairs)
    found = session.explorer.find_in_search_result_pages([first["name"], second["name"]])

    def _where(doc_name: str) -> str:
        return f"shown (page {found[doc_name]})" if doc_name in found else "not shown"

    ok = first["name"] in found and second["name"] in found
    return ok, (
        f"Match All off: first document {_where(first['name'])}, "
        f"second document {_where(second['name'])} (expected both documents)"
    )


SCENARIOS = [("Match All disabled", advanced)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
