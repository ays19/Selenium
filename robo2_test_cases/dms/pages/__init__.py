"""Selenium Page Object Model classes for the Robo2mation DMS test suite."""
from .base_page import BasePage, SetupError
from .bulk_upload_page import BulkUploadPage
from .categorization_page import CategorizationPage
from .document_view_page import DocumentViewPage
from .explorer_page import ExplorerPage
from .login_page import LoginError, LoginPage
from .master_table_page import MasterTablePage
from .review_page import ReviewPage
from .upload_page import UploadPage

__all__ = [
    "BasePage",
    "BulkUploadPage",
    "CategorizationPage",
    "DocumentViewPage",
    "ExplorerPage",
    "LoginError",
    "LoginPage",
    "MasterTablePage",
    "ReviewPage",
    "SetupError",
    "UploadPage",
]
