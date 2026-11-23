"""
DMS-TC012	Document Name Convention
"1. Go to https://ecmv6.robo2mation.com/dms/document/upload/standard_upload/filesave/pendingmetalist/
2. Attach a document (image, media or office file), select doc-type (which has document name convention), give all required meta-data value & give unique value to unique field.
3. Click on ""Save"" button"
Document name should be auto selected with the combination of meta data as per configuration
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC012"


def document_name_convention(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = os.getenv("NAME_CONVENTION_DOC_TYPE", "").strip()
    pending_name = session.upload.prepare_upload("pdf", doc_type)
    selected = session.upload.current_doc_type()
    selected_norm = selected.strip("/").lower()
    wanted_norm = doc_type.strip("/").lower()
    if selected_norm != wanted_norm and selected_norm.split("/")[-1] != wanted_norm:
        raise c.SetupError(f"doc-type '{doc_type}' was not selected (the page shows '{selected}')")

    convention = session.upload.convention_of_selected_doc_type()
    if not convention:
        raise c.SetupError(
            f"doc-type '{doc_type}' has no document name convention. Set NAME_CONVENTION_DOC_TYPE in .env"
        )
    session.upload.fill_convention_fields(session.upload.convention_fields(convention))
    session.upload.focus_file_name_for_convention()

    field_vals, created_date = session.upload.form_field_values()
    if not field_vals:
        raise c.SetupError("no meta-data value was filled for this doc-type")

    expected_name = session.upload.expected_convention_name(pending_name, convention, field_vals, created_date)
    matched, name = session.upload.wait_exact_file_name(expected_name)
    if not matched:
        return False, f"Document name '{name}' did not match expected '{expected_name}' (convention {convention})"

    ok, message = session.upload.click_save_upload()
    if not ok:
        return False, f"Document name was '{name}' but Save failed ({message})"
    if not session.explorer.search_finds(name, tries=5):
        return False, f"Document saved, but not found in search with the name '{name}'"

    return True, (
        f"Document name auto-selected as '{name}' matching '{expected_name}' (convention {convention}); "
        "saved and found in search"
    )


SCENARIOS = [("Document name convention", document_name_convention)]


def main() -> None:
    c.run_dms_test(
        TEST_CASE_ID,
        SCENARIOS,
        doc=__doc__,
        required_env=[("NAME_CONVENTION_DOC_TYPE", "(the doc-type that has a document name convention)")],
    )


if __name__ == "__main__":
    main()
