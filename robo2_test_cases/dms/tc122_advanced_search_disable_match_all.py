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
from datetime import datetime

import common as c

TEST_CASE_ID = "DMS-TC122"


def advanced(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = c.cfg.DOC_TYPE_SEARCH_TERMS[0]
    run = datetime.now().strftime("%H%M%S")
    val_a = f"AUTO_MALL_{run}_A"
    val_b = f"AUTO_MALL_{run}_B"
    val_other = f"AUTO_MALL_{run}_X"

    doc_one = datetime.now().strftime("AUTO_ONE_%H%M%S%f")
    session.upload.prepare_upload("pdf", doc_type)
    resolved_dt = session.upload.current_doc_type()
    pairs = session.upload.filled_values()
    if len(pairs) < 2:
        raise c.SetupError(f"Doc type '{resolved_dt}' needs >= 2 text metadata fields (got {pairs})")
    lbl1, lbl2 = pairs[0][0], pairs[1][0]
    session.upload.fill_field(lbl1, val_a)
    session.upload.fill_field(lbl2, val_other)
    session.upload.set_document_name(doc_one)
    ok1, msg1 = session.upload.click_save_upload()
    if not ok1:
        raise c.SetupError(f"first upload failed ({msg1})")

    doc_two = datetime.now().strftime("AUTO_TWO_%H%M%S%f")
    session.upload.prepare_upload("pdf", doc_type)
    session.upload.fill_field(lbl1, val_a)
    session.upload.fill_field(lbl2, val_b)
    session.upload.set_document_name(doc_two)
    ok2, msg2 = session.upload.click_save_upload()
    if not ok2:
        raise c.SetupError(f"second upload failed ({msg2})")

    session.explorer.open()
    session.explorer.advanced_search(
        None,
        match_all=False,
        doc_type=resolved_dt,
        extra=[(lbl1, val_a), (lbl2, val_b)],
    )
    ordered = session.explorer.advanced_search_result_names(max_pages=10)
    idx_two = next((i for i, n in enumerate(ordered) if doc_two.lower() in n.lower()), None)
    idx_one = next((i for i, n in enumerate(ordered) if doc_one.lower() in n.lower()), None)

    ok = idx_two is not None and idx_one is not None and idx_two < idx_one
    return ok, (
        f"Match All off: 2-match '{doc_two}' at pos {idx_two}, 1-match '{doc_one}' at pos {idx_one} "
        f"(total rows scanned={len(ordered)})"
    )


SCENARIOS = [("Match All disabled", advanced)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
