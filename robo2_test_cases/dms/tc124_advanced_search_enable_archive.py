"""
DMS-TC124
Advanced Search (Enable Archive)
1. Click on global search arrow icon
2. Select doc type
3. Give metadata
4. Enable "Include Archive"
5. Click on "Search"
Searched result should be shown including archived docs
"""
import common as c

TEST_CASE_ID = "DMS-TC124"


def include_archive(session: c.DmsSession) -> tuple[bool, str]:
    info = session.new_document()
    name = info["name"]
    ok, message = session.document.archive()
    if not ok:
        raise c.SetupError(f"could not archive the test document ({message})")

    without = session.explorer.advanced_finds(name, doc_type=info["doc_type"])
    with_archive = session.explorer.advanced_finds(name, doc_type=info["doc_type"], include_archive=True)
    ok = with_archive and not without
    return ok, (
        f"Archived document: found with Include Archive {'yes' if with_archive else 'NO'}, "
        f"found without it {'YES' if without else 'no'}"
    )


SCENARIOS = [("Include archive", include_archive)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
