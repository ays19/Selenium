"""
DMS-TC090
Metadata Uniqueness
1. Go to https://ecmv6.robo2mation.com/dms/document/root
2. Double click on a doc-type
3. Click on "More" button
4. Click on "Uniqueness Check"
5. Add a single field as "unique"
System shouldn't allow to upload/edit document with same value on this field & gave proper error message.
"""
from datetime import datetime

import common as c

TEST_CASE_ID = "DMS-TC090"
_DUP_WORDS = ("unique", "already", "exist", "duplicate")


def single_field(session: c.DmsSession) -> tuple[bool, str]:
    doc_type, fields = session.categorization.setup_uniqueness_doc_type(operator=None)
    field = fields[0]
    run_id = datetime.now().strftime("%H%M%S")
    v1, v2 = f"AUTO_U1_{run_id}", f"AUTO_U2_{run_id}"
    doc2_name = f"AUTO_UNIQ_DOC2_{run_id}"

    ok1, msg1 = session.upload.upload_with_values(doc_type, {field: v1})
    if not ok1:
        raise c.SetupError(f"first document did not upload ({msg1})")

    ok_dup, msg_dup = session.upload.upload_with_values(doc_type, {field: v1})
    has_dup_err = any(w in (msg_dup or "").lower() for w in _DUP_WORDS)

    ok2, msg2 = session.upload.upload_with_values(doc_type, {field: v2}, doc_name=doc2_name)
    if not ok2:
        raise c.SetupError(f"second unique document did not upload ({msg2})")

    main_tab = session.driver.current_window_handle
    try:
        session.explorer.open_document(doc2_name)
        ok_edit, msg_edit = session.document.edit_metadata_values({field: v1})
    finally:
        session.document.close_extra_tabs(main_tab)
    has_edit_err = any(w in (msg_edit or "").lower() for w in _DUP_WORDS)

    passed = (not ok_dup) and has_dup_err and (not ok_edit) and has_edit_err
    return passed, (
        f"Duplicate upload rejected={not ok_dup} ({msg_dup}); "
        f"Duplicate edit rejected={not ok_edit} ({msg_edit})"
    )


SCENARIOS = [("Single unique field", single_field)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
