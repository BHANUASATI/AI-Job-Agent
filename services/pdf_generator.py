"""
PDF generator service for enhanced resumes.

Generates PDF resumes from text content using ReportLab.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from utils.logger import get_logger
from config.settings import Config

logger = get_logger(__name__)


def generate_pdf_from_text(content: str, output_path: str) -> str:
    """
    Generate a PDF from text content.
    
    Args:
        content: Resume text content
        output_path: Path where PDF should be saved
    
    Returns:
        Path to generated PDF
    """
    try:
        logger.info(f"Generating PDF at {output_path}")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor='black'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            spaceBefore=12,
            textColor='black'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            leading=14
        )
        
        # Build content
        story = []
        
        # Split content into lines and process
        lines = content.split('\n')
        current_section = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_section:
                    # Add accumulated paragraph
                    paragraph_text = ' '.join(current_section)
                    if paragraph_text:
                        story.append(Paragraph(paragraph_text, normal_style))
                        story.append(Spacer(1, 6))
                    current_section = []
                continue
            
            # Check if this looks like a heading (all caps or ends with colon)
            if line.isupper() or line.endswith(':') or len(line) < 50 and line.isupper():
                # Add any accumulated content first
                if current_section:
                    paragraph_text = ' '.join(current_section)
                    if paragraph_text:
                        story.append(Paragraph(paragraph_text, normal_style))
                        story.append(Spacer(1, 6))
                    current_section = []
                
                # Add as heading
                story.append(Paragraph(line, heading_style))
                story.append(Spacer(1, 6))
            else:
                current_section.append(line)
        
        # Add remaining content
        if current_section:
            paragraph_text = ' '.join(current_section)
            if paragraph_text:
                story.append(Paragraph(paragraph_text, normal_style))
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"PDF generated successfully at {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error generating PDF: {e}", exc_info=True)
        raise


def generate_enhanced_resume_pdf(enhanced_content: str, original_resume_path: str, company: str, role: str) -> str:
    """
    Generate a PDF for enhanced resume with a descriptive filename.
    
    Args:
        enhanced_content: Enhanced resume text content
        original_resume_path: Path to original resume
        company: Company name
        role: Job role
    
    Returns:
        Path to generated PDF
    """
    try:
        # Create output directory
        output_dir = Config.GENERATED_RESUME_DIR if hasattr(Config, 'GENERATED_RESUME_DIR') else Config.RESUME_DIR / "generated"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate safe filename
        safe_company = "".join(c for c in company if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
        safe_role = "".join(c for c in role if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
        
        # Create filename
        original_name = os.path.splitext(os.path.basename(original_resume_path))[0]
        filename = f"{original_name}_enhanced_{safe_company}_{safe_role}.pdf"
        output_path = output_dir / filename
        
        # Generate PDF
        pdf_path = generate_pdf_from_text(enhanced_content, str(output_path))
        
        logger.info(f"Enhanced resume PDF generated at {pdf_path}")
        return pdf_path
        
    except Exception as e:
        logger.error(f"Error generating enhanced resume PDF: {e}", exc_info=True)
        raise
