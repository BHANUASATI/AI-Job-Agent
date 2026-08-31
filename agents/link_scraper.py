import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re


def extract_job_description(url):
    """
    Extract job description from a job posting URL.
    
    Args:
        url: URL of the job posting
    
    Returns:
        String containing the job description text
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try different selectors for job descriptions
        jd_text = ""
        
        # Common selectors for job descriptions
        selectors = [
            'div[class*="job-description"]',
            'div[class*="description"]',
            'div[class*="job-details"]',
            'section[class*="job"]',
            'div[id*="job-description"]',
            'div[id*="description"]',
            'div[class*="posting"]',
            'article',
            'main'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                jd_text = ' '.join([elem.get_text(separator=' ', strip=True) for elem in elements])
                if len(jd_text) > 200:  # Only use if we got substantial text
                    break
        
        # Fallback: get body text if no specific selector worked
        if not jd_text or len(jd_text) < 200:
            body = soup.find('body')
            if body:
                jd_text = body.get_text(separator=' ', strip=True)
        
        # Clean up the text
        jd_text = re.sub(r'\s+', ' ', jd_text)
        jd_text = jd_text.strip()
        
        return jd_text
        
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return ""
    except Exception as e:
        print(f"Error parsing job description: {e}")
        return ""


def is_job_url(url):
    """
    Check if URL is likely a job posting URL.
    
    Args:
        url: URL to check
    
    Returns:
        Boolean indicating if URL is likely a job posting
    """
    job_keywords = [
        'job', 'career', 'position', 'opening', 'vacancy',
        'hiring', 'apply', 'recruit', 'listing', 'posting'
    ]
    
    url_lower = url.lower()
    
    # Check for job-related keywords in URL
    for keyword in job_keywords:
        if keyword in url_lower:
            return True
    
    # Check for common job board domains
    job_domains = [
        'linkedin.com/jobs',
        'indeed.com',
        'glassdoor.com',
        'monster.com',
        'ziprecruiter.com',
        'angel.co',
        'wellfound.com',
        'internshala.com',
        'naukri.com'
    ]
    
    for domain in job_domains:
        if domain in url_lower:
            return True
    
    return False


def scrape_job_link(url):
    """
    Scrape job description from a job link.
    
    Args:
        url: Job posting URL
    
    Returns:
        Dictionary with job description text and metadata
    """
    if not is_job_url(url):
        return {
            "success": False,
            "error": "URL does not appear to be a job posting"
        }
    
    jd_text = extract_job_description(url)
    
    if not jd_text:
        return {
            "success": False,
            "error": "Could not extract job description"
        }
    
    return {
        "success": True,
        "url": url,
        "job_description": jd_text,
        "length": len(jd_text)
    }
