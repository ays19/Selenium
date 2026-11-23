"""
DMS-TC091
Metadata Uniqueness
1. Go to https://ecmv6.robo2mation.com/dms/document/root
2. Double click on a doc-type
3. Click on "More" button
4. Click on "Uniqueness Check"
5. Add multiple field as "unique" & separating them with "OR"
System shouldn't allow to upload/edit document with same value on any of these fields & gave proper error message.
Notes: Only allowed to upload/edit if all of these fields value are unique
"""
from datetime import datetime

import common as c

TEST_CASE_ID = "DMS-TC091"
_DUP_WORDS = ("unique", "already", "exist", "duplicate")


def unique_or(session: c.DmsSession) -> tuple[bool, str]:
    doc_type, (first, second) = session.categorization.setup_uniqueness_doc_type(operator="or")
    run_id = datetime.now().strftime("%H%M%S")
    a1, b1 = f"AUTO_A{run_id}", f"AUTO_B{run_id}"
    doc2_name = f"AUTO_OR_DOC2_{run_id}"

    ok, message = session.upload.upload_with_values(doc_type, {first: a1, second: b1})
    if not ok:
        raise c.SetupError(f"first document did not upload ({message})")

    same_first, msg_first = session.upload.upload_with_values(doc_type, {first: a1, second: f"AUTO_C{run_id}"})
    same_second, msg_second = session.upload.upload_with_values(doc_type, {first: f"AUTO_D{run_id}", second: b1})
    all_new, msg_new = session.upload.upload_with_values(
        doc_type, {first: f"AUTO_E{run_id}", second: f"AUTO_F{run_id}"}, doc_name=doc2_name
    )

    main_tab = session.driver.current_window_handle
    try:
        session.explorer.open_document(doc2_name)
        ok_edit, msg_edit = session.document.edit_metadata_values({first: a1, second: f"AUTO_G{run_id}"})
    finally:
        session.document.close_extra_tabs(main_tab)

    err_first = any(w in (msg_first or "").lower() for w in _DUP_WORDS)
    err_second = any(w in (msg_second or "").lower() for w in _DUP_WORDS)
    err_edit = any(w in (msg_edit or "").lower() for w in _DUP_WORDS)

    passed = (
        (not same_first) and err_first
        and (not same_second) and err_second
        and all_new
        and (not ok_edit) and err_edit
    )
    return passed, (
        f"Same field1 rejected={not same_first} ({msg_first}); "
        f"Same field2 rejected={not same_second} ({msg_second}); "
        f"All new accepted={all_new} ({msg_new}); "
        f"Edit same field1 rejected={not ok_edit} ({msg_edit})"
    )


SCENARIOS = [("Unique fields with OR", unique_or)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
