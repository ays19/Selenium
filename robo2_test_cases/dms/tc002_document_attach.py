"""
DMS-TC002
Document Attach
1. Go to https://ecmv6.robo2mation.com/dms/document/upload/standard_upload/
2. Attach documents (PDF, PNG, JPG, JPEG, SVG, GIF, MP3, MP4, DOC, DOCX, XLS, XLSX, CSV, PPT, PPTX, MSG, EML, TXT) less than 20 mb
System should allow to attach documents (media or office file)
"""
import common as c

TEST_CASE_ID = "DMS-TC002"


def attach_ext(ext: str):
    def _scenario(session: c.DmsSession) -> tuple[bool, str]:
        return session.upload.attach_file_check(ext)

    return _scenario


def summarize(results: list[tuple[str, bool, str]]) -> str:
    total = len(results)
    failed = [f"{lbl} ({msg})" for lbl, ok, msg in results if not ok]
    if failed:
        passed_count = total - len(failed)
        return f"Attached {passed_count}/{total} file types. Could not attach: " + ", ".join(failed)
    return f"All {total} file types were attached successfully"


SCENARIOS = [(ext, attach_ext(ext)) for ext in c.EXTENSIONS]


def main() -> None:
    missing_files = [ext for ext in c.EXTENSIONS if not c.UploadPage.find_sample_file(ext)]
    print(f"Files missing in {c.SAMPLE_DIR}: {missing_files or 'none'}")
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__, summary_fn=summarize)


if __name__ == "__main__":
    main()
