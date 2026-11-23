"""
DMS-TC092
Metadata Uniqueness
1. Go to https://ecmv6.robo2mation.com/dms/document/root
2. Double click on a doc-type
3. Click on "More" button
4. Click on "Uniqueness Check"
5. Add multiple field as "unique" & separating them with "AND"
System shouldn't allow to upload/edit document with same value on all of these fields & gave proper error message.
Notes: Only allowed to upload/edit if any of these fields value are unique
"""
from datetime import datetime

import common as c

TEST_CASE_ID = "DMS-TC092"
_DUP_WORDS = ("unique", "already", "exist", "duplicate")


def unique_and(session: c.DmsSession) -> tuple[bool, str]:
    doc_type, (first, second) = session.categorization.setup_uniqueness_doc_type(operator="and")
    run_id = datetime.now().strftime("%H%M%S")
    a1, b1 = f"AUTO_A{run_id}", f"AUTO_B{run_id}"
    doc2_name = f"AUTO_AND_DOC2_{run_id}"

    ok, message = session.upload.upload_with_values(doc_type, {first: a1, second: b1})
    if not ok:
        raise c.SetupError(f"first document did not upload ({message})")

    same_all, msg_all = session.upload.upload_with_values(doc_type, {first: a1, second: b1})
    one_new, msg_new = session.upload.upload_with_values(
        doc_type, {first: a1, second: f"AUTO_C{run_id}"}, doc_name=doc2_name
    )

    main_tab = session.driver.current_window_handle
    try:
        session.explorer.open_document(doc2_name)
        ok_edit, msg_edit = session.document.edit_metadata_values({first: a1, second: b1})
    finally:
        session.document.close_extra_tabs(main_tab)

    err_all = any(w in (msg_all or "").lower() for w in _DUP_WORDS)
    err_edit = any(w in (msg_edit or "").lower() for w in _DUP_WORDS)

    passed = (not same_all) and err_all and one_new and (not ok_edit) and err_edit
    return passed, (
        f"Same all rejected={not same_all} ({msg_all}); "
        f"One field different accepted={one_new} ({msg_new}); "
        f"Edit same all rejected={not ok_edit} ({msg_edit})"
    )


SCENARIOS = [("Unique fields with AND", unique_and)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
