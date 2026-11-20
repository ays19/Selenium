"""
DMS-TC003
Document View in Pending Documents (Grid View)
1. Go to https://ecmv6.robo2mation.com/dms/document/upload/standard_upload/filesave/pendingmetalist/
2. Click on "Grid View" icon
3. Click on "view document" icon (PDF, PNG, JPG, JPEG, SVG, GIF, MP3, MP4, DOC, DOCX, XLS, XLSX, CSV, PPT, PPTX, MSG, EML, TXT file)
System should allow to view the document and if give user a message if preview not available
"""
import common as c

TEST_CASE_ID = "DMS-TC003"


def view_ext(ext: str):
    def _scenario(session: c.DmsSession) -> tuple[bool, str]:
        return session.upload.view_pending_document(ext)

    return _scenario


def summarize(results: list[tuple[str, bool, str]]) -> str:
    total = len(results)
    failed = [f"{lbl} ({msg})" for lbl, ok, msg in results if not ok]
    if failed:
        passed_count = total - len(failed)
        return f"Viewed {passed_count}/{total} file types. Could not view: " + ", ".join(failed)
    return f"All {total} file types opened in preview, or showed a preview not available message"


SCENARIOS = [(ext, view_ext(ext)) for ext in c.EXTENSIONS]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__, summary_fn=summarize)


if __name__ == "__main__":
    main()
