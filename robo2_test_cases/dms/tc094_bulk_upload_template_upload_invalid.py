"""
DMS-TC094
Bulk Upload Template Upload
1. Go to https://ecmv6.robo2mation.com/dms/document/upload/bulk-upload/
2. Type & select a doc-type
3. upload bulk upload template csv (blank/same value in unique metadata/wrong formated data/wrong type attachment)
System shouldn't allow to upload documents & give proper error in "Bulk Upload Report"
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC094"


def rejected(label: str, make_file):
    def _scenario(session: c.DmsSession) -> tuple[bool, str]:
        doc_type = os.getenv("BULK_DOC_TYPE", "").strip()
        template = session.bulk_upload.download_template(doc_type)
        header = session.bulk_upload.template_header(template)
        path = make_file(session, header)
        ok, message = session.bulk_upload.bulk_submit(doc_type, path)
        error_shown = (not ok) or "error" in session.bulk_upload.body_text()
        return error_shown, f"{label} file " + (
            f"was rejected: {message}" if error_shown else f"was ACCEPTED: {message}"
        )

    return _scenario


def blank_file(session: c.DmsSession, header: list[str]) -> str:
    return session.bulk_upload.write_csv(
        os.path.join(c.DOWNLOAD_DIR, "AUTO_blank.csv"), header, [[""] * len(header)]
    )


def same_value_file(session: c.DmsSession, header: list[str]) -> str:
    row = ["AUTO_SAME"] * len(header)
    return session.bulk_upload.write_csv(
        os.path.join(c.DOWNLOAD_DIR, "AUTO_same.csv"), header, [row, row]
    )


def wrong_format_file(session: c.DmsSession, header: list[str]) -> str:
    return session.bulk_upload.write_csv(
        os.path.join(c.DOWNLOAD_DIR, "AUTO_format.csv"), header, [["!!bad!!"] * len(header)]
    )


def wrong_type_file(session: c.DmsSession, header: list[str]) -> str:
    sample = session.upload.find_sample_file("png")
    if not sample:
        raise c.SetupError(f"no .png sample file in {c.SAMPLE_DIR}")
    return sample[1]


SCENARIOS = [
    ("Blank data", rejected("Blank", blank_file)),
    ("Same unique value", rejected("Same value", same_value_file)),
    ("Wrong format data", rejected("Wrong format", wrong_format_file)),
    ("Wrong type attachment", rejected("Wrong type", wrong_type_file)),
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
