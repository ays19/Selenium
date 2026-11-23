"""
DMS-TC033
Share Documents (External Share)
1. Go to "Pending Documents/Document View" page
2. Select public
3. Click on "Share" button
Documents should be shared with all system users & anyone with the link can access those documents.
"""
import urllib.request

import common as c

TEST_CASE_ID = "DMS-TC033"


def _check_public_url(url: str) -> tuple[bool, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        final_url = resp.geturl().lower()
        code = resp.getcode()
    if code != 200 or "/login" in final_url:
        return False, f"public URL returned HTTP {code} at '{final_url}'"
    return True, f"public URL accessible without login (HTTP {code})"


def share_public(session: c.DmsSession) -> tuple[bool, str]:
    info = session.new_document("pdf")
    name = info["name"]
    ok, msg, share_url = session.document.share_on_document_view("public")
    if not ok:
        return False, msg
    if "/dms/document/public/view/" not in share_url:
        share_url = session.document.read_share_link_input()
    if "/dms/document/public/view/" not in share_url:
        return False, f"expected '/dms/document/public/view/' in share URL, got '{share_url}'"

    access_ok, access_msg = _check_public_url(share_url)
    icons = session.explorer.explorer_doc_icons(info["doc_type"], name)
    passed = access_ok and icons["found"] and icons["shared"]
    return passed, f"{msg}; {access_msg}; Explorer shared icon: {'yes' if icons['shared'] else 'NO'}"


SCENARIOS = [("Public share", share_public)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
