"""
DMS-TC094
Bulk Upload Template Upload
1. Go to https://ecmv6.robo2mation.com/dms/document/upload/bulk-upload/
2. Type & select a doc-type
3. upload bulk upload template csv (blank/same value in unique metadata/wrong formated data/wrong type attachment)
System shouldn't allow to upload documents & give proper error in "Bulk Upload Report"
"""
from datetime import datetime
import os

import common as c

TEST_CASE_ID = "DMS-TC094"


def rejected(label: str, make_file, expected_keywords: tuple[str, ...], forbidden_keywords: tuple[str, ...] = ()):
    def _scenario(session: c.DmsSession) -> tuple[bool, str]:
        doc_type = os.getenv("BULK_DOC_TYPE", "").strip()
        template = session.bulk_upload.download_template(doc_type)
        header = session.bulk_upload.template_header(template)
        doc_id = session.bulk_upload.selected_doc_type_id()
        meta_fields, unique_vals = session.bulk_upload.fetch_metadata_and_unique_values(doc_id)
        date_fmt = session.bulk_upload.system_date_format()

        path = make_file(session, header, meta_fields, unique_vals, date_fmt)
        ok, message = session.bulk_upload.bulk_submit(doc_type, path)
        report = session.bulk_upload.parse_upload_report()
        combined = f"{message} | {report}".lower()

        has_expected = any(kw in combined for kw in expected_keywords)
        has_forbidden = any(kw in combined for kw in forbidden_keywords)
        passed = (not ok) and has_expected and not has_forbidden
        return passed, f"{label} rejected={not ok}, expected={has_expected}, unexpected_errs={has_forbidden}: {message}"

    return _scenario


def blank_file(session: c.DmsSession, header: list[str], *_args) -> str:
    return session.bulk_upload.write_csv(
        os.path.join(c.DOWNLOAD_DIR, "AUTO_blank.csv"), header, [[""] * len(header)]
    )


def same_value_file(session: c.DmsSession, header: list[str], meta_fields: dict, unique_vals: dict, date_fmt: str) -> str:
    run_id = datetime.now().strftime("%H%M%S")
    used_unique = {k: set(str(v) for v in vals if v is not None) for k, vals in unique_vals.items()}
    rows = session.bulk_upload.build_duplicate_unique_rows(
        header, "a.pdf", "b.pdf", run_id, meta_fields, used_unique, date_fmt
    )
    return session.bulk_upload.write_csv(os.path.join(c.DOWNLOAD_DIR, "AUTO_same.csv"), header, rows)


def wrong_format_file(session: c.DmsSession, header: list[str], meta_fields: dict, unique_vals: dict, date_fmt: str) -> str:
    run_id = datetime.now().strftime("%H%M%S")
    used_unique = {k: set(str(v) for v in vals if v is not None) for k, vals in unique_vals.items()}
    row = session.bulk_upload.build_wrong_format_row(header, "a.pdf", run_id, meta_fields, used_unique, date_fmt)
    return session.bulk_upload.write_csv(os.path.join(c.DOWNLOAD_DIR, "AUTO_format.csv"), header, [row])


def wrong_type_file(session: c.DmsSession, *_args) -> str:
    sample = session.upload.find_sample_file("png")
    if not sample:
        raise c.SetupError(f"no .png sample file in {c.SAMPLE_DIR}")
    return sample[1]


SCENARIOS = [
    ("Blank data", rejected("Blank", blank_file, ("is required",))),
    (
        "Same unique value",
        rejected(
            "Same unique",
            same_value_file,
            ("should be unique",),
            forbidden_keywords=("should be integer", "should be decimal", "has invalid data"),
        ),
    ),
    (
        "Wrong format data",
        rejected("Wrong format", wrong_format_file, ("should be integer", "should be decimal", "invalid data", "wrong date")),
    ),
    ("Wrong type attachment", rejected("Wrong type", wrong_type_file, ("upload csv",))),
]


def main() -> None:
    c.run_dms_test(
        TEST_CASE_ID,
        SCENARIOS,
        doc=__doc__,
        required_env=[("BULK_DOC_TYPE", "(search text of a doc-type for bulk upload)")],
    )


if __name__ == "__main__":
    main()
