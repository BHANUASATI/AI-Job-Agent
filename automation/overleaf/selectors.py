"""
CSS selectors for Overleaf automation.

All selectors are centralized here for easy maintenance and updates.
Uses robust selectors preferring data-testid, aria-label, and role attributes
over fragile XPath or class-based selectors.
"""


class OverleafSelectors:
    """Centralized CSS selectors for Overleaf automation."""
    
    # ============================================================================
    # Login Page Selectors
    # ============================================================================
    
    LOGIN_BUTTON = 'a[href="/login"], a:has-text("Log in"), button:has-text("Log in")'
    LOGIN_PAGE_EMAIL_INPUT = 'input[name="email"], input[type="email"], input#email'
    LOGIN_PAGE_PASSWORD_INPUT = 'input[name="password"], input[type="password"], input#password'
    LOGIN_PAGE_SUBMIT_BUTTON = 'button[type="submit"], button:has-text("Log in"), button:has-text("Sign in")'
    LOGIN_PAGE_GOOGLE_BUTTON = 'button[data-provider="google"], button:has-text("Google")'
    LOGIN_PAGE_ORCID_BUTTON = 'button[data-provider="orcid"], button:has-text("ORCID")'
    
    # ============================================================================
    # Dashboard Selectors
    # ============================================================================
    
    DASHBOARD_CONTAINER = 'div.dashboard, div[data-reactid*="dashboard"], main, body'
    PROJECT_LIST = 'div.project-list, ul.project-list, div[data-reactid*="project-list"], div[class*="project"]'
    PROJECT_ITEM = 'div.project-list-item, li.project-list-item, div.project-card, div[class*="project-item"]'
    PROJECT_LINK = 'a.project-link, a[href*="/project"], a[href*="project"]'
    PROJECT_NAME = 'span.project-name, h3, h4, .project-title, div[class*="name"], div[class*="title"]'
    NEW_PROJECT_BUTTON = 'button[data-testid="new-project-button"], button:has-text("New Project")'
    
    # ============================================================================
    # Project Editor Selectors
    # ============================================================================
    
    EDITOR_CONTAINER = 'div.editor-container'
    EDITOR_TEXT_AREA = 'textarea.ace_text-input'
    EDITOR_CONTENT = 'div.ace_content'
    FILE_TREE = 'div.file-tree'
    FILE_TREE_ITEM = 'div.file-tree-item'
    FILE_NAME = 'span.file-name'
    FILE_LIST_ITEM = 'li.file-list-item'
    
    # ============================================================================
    # File Operations Selectors
    # ============================================================================
    
    NEW_FILE_BUTTON = 'button[data-testid="new-file-button"]'
    UPLOAD_FILE_BUTTON = 'button[data-testid="upload-file-button"]'
    FILE_MENU_BUTTON = 'button.file-menu-button'
    DELETE_FILE_BUTTON = 'button[data-testid="delete-file-button"]'
    RENAME_FILE_BUTTON = 'button[data-testid="rename-file-button"]'
    
    # ============================================================================
    # Compile/Recompile Selectors
    # ============================================================================
    
    RECOMPILE_BUTTON = 'button[data-testid="recompile-button"]'
    COMPILE_STATUS = 'div.compile-status'
    COMPILE_SUCCESS = 'div.compile-status[data-status="success"]'
    COMPILE_ERROR = 'div.compile-status[data-status="error"]'
    COMPILE_LOG = 'div.compile-log'
    COMPILE_LOG_OUTPUT = 'pre.compile-log-output'
    
    # ============================================================================
    # PDF Preview Selectors
    # ============================================================================
    
    PDF_PREVIEW_CONTAINER = 'div.pdf-preview-container'
    PDF_VIEWER = 'iframe.pdf-viewer'
    PDF_DOWNLOAD_BUTTON = 'button[data-testid="pdf-download-button"]'
    PDF_DOWNLOAD_LINK = 'a[href$=".pdf"]'
    
    # ============================================================================
    # Editor Toolbar Selectors
    # ============================================================================
    
    EDITOR_TOOLBAR = 'div.editor-toolbar'
    SAVE_BUTTON = 'button[data-testid="save-button"]'
    AUTOSAVE_INDICATOR = 'div.autosave-indicator'
    AUTOSAVE_SAVED = 'div.autosave-indicator[data-status="saved"]'
    AUTOSAVE_SAVING = 'div.autosave-indicator[data-status="saving"]'
    
    # ============================================================================
    # Navigation Selectors
    # ============================================================================
    
    HOME_LINK = 'a[href="/"]'
    DASHBOARD_LINK = 'a[href="/dashboard"]'
    USER_MENU = 'button.user-menu-button'
    LOGOUT_BUTTON = 'button[data-testid="logout-button"]'
    
    # ============================================================================
    # Modal/Dialog Selectors
    # ============================================================================
    
    MODAL_CONTAINER = 'div.modal-container'
    MODAL_TITLE = 'h2.modal-title'
    MODAL_CLOSE_BUTTON = 'button.modal-close-button'
    MODAL_CONFIRM_BUTTON = 'button.modal-confirm-button'
    MODAL_CANCEL_BUTTON = 'button.modal-cancel-button'
    
    # ============================================================================
    # Error/Notification Selectors
    # ============================================================================
    
    ERROR_MESSAGE = 'div.error-message'
    WARNING_MESSAGE = 'div.warning-message'
    SUCCESS_MESSAGE = 'div.success-message'
    NOTIFICATION = 'div.notification'
    NOTIFICATION_CLOSE = 'button.notification-close'
    
    # ============================================================================
    # Loading Selectors
    # ============================================================================
    
    LOADING_SPINNER = 'div.loading-spinner'
    LOADING_OVERLAY = 'div.loading-overlay'
    SKELETON_LOADER = 'div.skeleton-loader'
    
    # ============================================================================
    # Specific File Selectors (for resume editing)
    # ============================================================================
    
    MASTER_RESUME_FILE = 'li.file-list-item:has-text("master_resume.tex")'
    MAIN_TEX_FILE = 'li.file-list-item:has-text("main.tex")'
    RESUME_TEX_FILE = 'li.file-list-item:has-text("resume.tex")'
    
    # ============================================================================
    # LaTeX Section Selectors (for content editing)
    # ============================================================================
    
    # These are used to identify sections in the LaTeX editor
    LATEX_SECTION_SKILLS = r'\\section\{Skills\}'
    LATEX_SECTION_EXPERIENCE = r'\\section\{Experience\}'
    LATEX_SECTION_PROJECTS = r'\\section\{Projects\}'
    LATEX_SECTION_CERTIFICATIONS = r'\\section\{Certifications\}'
    LATEX_SECTION_SUMMARY = r'\\section\{Summary\}'
    LATEX_SECTION_EDUCATION = r'\\section\{Education\}'
    
    # ============================================================================
    # Helper Methods
    # ============================================================================
    
    @staticmethod
    def get_project_selector(project_name: str) -> str:
        """
        Get selector for a specific project by name.
        
        Args:
            project_name: Name of the project
            
        Returns:
            CSS selector for the project
        """
        return f'div.project-list-item:has-text("{project_name}")'
    
    @staticmethod
    def get_file_selector(filename: str) -> str:
        """
        Get selector for a specific file by name.
        
        Args:
            filename: Name of the file
            
        Returns:
            CSS selector for the file
        """
        return f'li.file-list-item:has-text("{filename}")'
    
    @staticmethod
    def get_section_selector(section_name: str) -> str:
        """
        Get LaTeX pattern for a specific section.
        
        Args:
            section_name: Name of the section
            
        Returns:
            LaTeX pattern for the section
        """
        section_map = {
            'skills': OverleafSelectors.LATEX_SECTION_SKILLS,
            'experience': OverleafSelectors.LATEX_SECTION_EXPERIENCE,
            'projects': OverleafSelectors.LATEX_SECTION_PROJECTS,
            'certifications': OverleafSelectors.LATEX_SECTION_CERTIFICATIONS,
            'summary': OverleafSelectors.LATEX_SECTION_SUMMARY,
            'education': OverleafSelectors.LATEX_SECTION_EDUCATION,
        }
        return section_map.get(section_name.lower(), f'\\section\\{{{section_name}\\}}')
