"""
DMS-TC080
Publish Doc-Type
1. Go to https://ecmv6.robo2mation.com/dms/document/root
2. Select a doc-type
3. Click on "publish" button
4. Select "published"
5. Click on "Save" button
1. Document type should be published with confirmation message
2. Document type should be accessible from permitted general user
"""
import common as c

TEST_CASE_ID = "DMS-TC080"


def publish(session: c.DmsSession) -> tuple[bool, str]:
    name = session.categorization.new_doc_type()
    return session.categorization.publish_doc_type(name)


SCENARIOS = [("Publish doc-type", publish)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
