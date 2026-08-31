"""
Database service module.

Provides database operations using configured settings.
Currently uses JSON file storage, will be migrated to SQLite.
"""

import json
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, ConfigDict
from config.settings import Config
from utils.logger import get_logger
from utils.exceptions import DatabaseError

logger = get_logger(__name__)


class JobApplication(BaseModel):
    id: str
    company: str
    role: str
    location: Optional[str]
    skills: List[str]
    experience: str
    email: str
    resume_used: str
    match_score: float
    gap_score: float
    status: str
    applied_date: str
    notes: Optional[str] = ""

    model_config = ConfigDict(arbitrary_types_allowed=True)


class DatabaseService:
    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DATABASE_DIR / "applications.json"
        self.applications = self._load_applications()
    
    def _load_applications(self) -> List[Dict]:
        """Load applications from JSON file."""
        try:
            if self.db_path.exists():
                with open(self.db_path, 'r') as f:
                    try:
                        data = json.load(f)
                        logger.info(f"Loaded {len(data)} applications from database")
                        return data
                    except (json.JSONDecodeError, IOError) as e:
                        logger.error(f"Error parsing database file: {e}")
                        return []
            return []
        except Exception as e:
            logger.error(f"Error loading applications: {e}", exc_info=True)
            return []
    
    def _save_applications(self):
        """Save applications to JSON file."""
        try:
            Config.DATABASE_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.db_path, 'w') as f:
                json.dump(self.applications, f, indent=2)
            logger.debug(f"Saved {len(self.applications)} applications to database")
        except Exception as e:
            logger.error(f"Error saving applications: {e}", exc_info=True)
            raise DatabaseError(f"Failed to save applications: {e}")
    
    def add_application(self, application: JobApplication) -> JobApplication:
        """Add a new job application."""
        try:
            self.applications.append(application.model_dump())
            self._save_applications()
            logger.info(f"Added application for {application.company} - {application.role}")
            return application
        except Exception as e:
            logger.error(f"Error adding application: {e}", exc_info=True)
            raise DatabaseError(f"Failed to add application: {e}")
    
    def get_all_applications(self) -> List[JobApplication]:
        """Get all job applications."""
        try:
            return [JobApplication(**app) for app in self.applications]
        except Exception as e:
            logger.error(f"Error getting applications: {e}", exc_info=True)
            raise DatabaseError(f"Failed to get applications: {e}")
    
    def get_application_by_id(self, app_id: str) -> Optional[JobApplication]:
        """Get application by ID."""
        try:
            for app in self.applications:
                if app['id'] == app_id:
                    return JobApplication(**app)
            return None
        except Exception as e:
            logger.error(f"Error getting application by ID: {e}", exc_info=True)
            raise DatabaseError(f"Failed to get application: {e}")
    
    def update_application_status(self, app_id: str, status: str) -> Optional[JobApplication]:
        """Update application status."""
        try:
            for app in self.applications:
                if app['id'] == app_id:
                    app['status'] = status
                    self._save_applications()
                    logger.info(f"Updated application {app_id} status to {status}")
                    return JobApplication(**app)
            return None
        except Exception as e:
            logger.error(f"Error updating application status: {e}", exc_info=True)
            raise DatabaseError(f"Failed to update application status: {e}")
    
    def delete_application(self, app_id: str) -> bool:
        """Delete application by ID."""
        try:
            for i, app in enumerate(self.applications):
                if app['id'] == app_id:
                    self.applications.pop(i)
                    self._save_applications()
                    logger.info(f"Deleted application {app_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error deleting application: {e}", exc_info=True)
            raise DatabaseError(f"Failed to delete application: {e}")
    
    def get_applications_by_company(self, company: str) -> List[JobApplication]:
        """Get applications by company."""
        try:
            return [
                JobApplication(**app) 
                for app in self.applications 
                if app['company'].lower() == company.lower()
            ]
        except Exception as e:
            logger.error(f"Error getting applications by company: {e}", exc_info=True)
            raise DatabaseError(f"Failed to get applications by company: {e}")
    
    def get_applications_by_status(self, status: str) -> List[JobApplication]:
        """Get applications by status."""
        try:
            return [
                JobApplication(**app) 
                for app in self.applications 
                if app['status'].lower() == status.lower()
            ]
        except Exception as e:
            logger.error(f"Error getting applications by status: {e}", exc_info=True)
            raise DatabaseError(f"Failed to get applications by status: {e}")
    
    def get_statistics(self) -> Dict:
        """Get application statistics."""
        try:
            total = len(self.applications)
            if total == 0:
                return {
                    "total": 0,
                    "by_status": {},
                    "by_company": {},
                    "by_domain": {},
                    "avg_match_score": 0
                }
            
            by_status = {}
            by_company = {}
            by_domain = {}
            total_score = 0
            
            for app in self.applications:
                # By status
                status = app['status']
                by_status[status] = by_status.get(status, 0) + 1
                
                # By company
                company = app['company']
                by_company[company] = by_company.get(company, 0) + 1
                
                # By domain (extract from role)
                role = app['role'].lower()
                domain = "Unknown"
                if "engineer" in role or "developer" in role:
                    domain = "Engineering"
                elif "data" in role or "analyst" in role:
                    domain = "Data"
                elif "product" in role or "manager" in role:
                    domain = "Product"
                elif "design" in role:
                    domain = "Design"
                elif "marketing" in role or "sales" in role:
                    domain = "Marketing/Sales"
                
                by_domain[domain] = by_domain.get(domain, 0) + 1
                
                # Score
                total_score += app.get('match_score', 0)
            
            return {
                "total": total,
                "by_status": by_status,
                "by_company": by_company,
                "by_domain": by_domain,
                "avg_match_score": total_score / total
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}", exc_info=True)
            raise DatabaseError(f"Failed to get statistics: {e}")
    
    def get_recent_applications(self, limit: int = 10) -> List[JobApplication]:
        """Get most recent applications."""
        try:
            sorted_apps = sorted(
                self.applications,
                key=lambda x: x.get('applied_date', ''),
                reverse=True
            )
            return [JobApplication(**app) for app in sorted_apps[:limit]]
        except Exception as e:
            logger.error(f"Error getting recent applications: {e}", exc_info=True)
            raise DatabaseError(f"Failed to get recent applications: {e}")


# Global instance
_db_service = None

def get_database_service() -> DatabaseService:
    """Get or create database service instance."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
