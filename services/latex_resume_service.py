"""
LaTeX Resume Service using local LaTeX compilation.

Generates professional LaTeX resumes using pdflatex and local templates.
"""

import subprocess
import os
import shutil
from typing import Dict, Any, Optional
from pathlib import Path
from utils.logger import get_logger
from config.settings import Config

logger = get_logger(__name__)


def generate_latex_resume_from_template(resume_content: str, template_path: str, output_path: str) -> str:
    """
    Generate a LaTeX resume by compiling a local template.
    
    Args:
        resume_content: Resume content to inject into template
        template_path: Path to LaTeX template file
        output_path: Path where PDF should be saved
    
    Returns:
        Path to generated PDF
    """
    try:
        logger.info(f"Generating LaTeX resume using local compilation")
        
        # Create temporary directory for compilation
        temp_dir = Path(output_path).parent / "temp_latex"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy template to temp directory
        template_name = Path(template_path).stem
        tex_path = temp_dir / f"{template_name}.tex"
        shutil.copy(template_path, tex_path)
        
        # Compile LaTeX to PDF
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(temp_dir), str(tex_path)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            logger.error(f"LaTeX compilation failed: {result.stderr}")
            raise RuntimeError(f"LaTeX compilation failed: {result.stderr}")
        
        # Move generated PDF to output path
        pdf_path = temp_dir / f"{template_name}.pdf"
        if pdf_path.exists():
            shutil.move(str(pdf_path), output_path)
        else:
            raise RuntimeError("PDF was not generated")
        
        # Clean up temporary files
        for ext in ['.aux', '.log', '.out']:
            temp_file = temp_dir / f"{template_name}{ext}"
            if temp_file.exists():
                temp_file.unlink()
        
        logger.info(f"LaTeX resume generated successfully at {output_path}")
        return output_path
        
    except subprocess.TimeoutExpired:
        logger.error("LaTeX compilation timed out")
        raise RuntimeError("LaTeX compilation timed out")
    except Exception as e:
        logger.error(f"Error generating LaTeX resume: {e}", exc_info=True)
        raise


def convert_text_to_latex(resume_content: str, user_profile: Dict[str, Any]) -> str:
    """
    Convert plain text resume content to LaTeX format.
    
    Args:
        resume_content: Plain text resume content
        user_profile: User profile information
    
    Returns:
        LaTeX formatted resume content
    """
    try:
        logger.info("Converting resume to LaTeX format")
        
        # Escape special LaTeX characters
        def escape_latex(text):
            replacements = {
                '&': r'\&',
                '%': r'\%',
                '$': r'\$',
                '#': r'\#',
                '_': r'\_',
                '{': r'\{',
                '}': r'\}',
                '~': r'\textasciitilde{}',
                '^': r'\^{}',
                '\\': r'\textbackslash{}',
            }
            for char, replacement in replacements.items():
                text = text.replace(char, replacement)
            return text
        
        # Convert plain text to LaTeX
        lines = resume_content.split('\n')
        latex_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                latex_lines.append('')
                continue
            
            # Detect section headers (all caps or ends with colon)
            if line.isupper() or line.endswith(':'):
                # Convert to LaTeX section
                section_name = line.rstrip(':').strip()
                latex_lines.append(f"\\section{{{escape_latex(section_name)}}}")
            elif line.startswith('-') or line.startswith('•') or line.startswith('*'):
                # Convert to itemize item
                item_text = line.lstrip('-•*').strip()
                latex_lines.append(f"\\item {escape_latex(item_text)}")
            else:
                # Regular paragraph
                latex_lines.append(escape_latex(line))
        
        latex_content = '\n'.join(latex_lines)
        logger.info("Resume converted to LaTeX format successfully")
        return latex_content
        
    except Exception as e:
        logger.error(f"Error converting resume to LaTeX format: {e}", exc_info=True)
        raise


def generate_enhanced_resume_latex(enhanced_content: str, original_resume_path: str, company: str, role: str, user_profile: Dict[str, Any]) -> str:
    """
    Generate an enhanced LaTeX resume using local LaTeX compilation.
    
    Args:
        enhanced_content: Enhanced resume text content
        original_resume_path: Path to original resume
        company: Company name
        role: Job role
        user_profile: User profile information
    
    Returns:
        Path to generated PDF
    """
    try:
        import os
        
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
        
        # Use existing LaTeX template
        template_path = Config.RESUME_TEMPLATES_DIR / "master_resume.tex" if hasattr(Config, 'RESUME_TEMPLATES_DIR') else Path("resume_templates/master_resume.tex")
        
        if not template_path.exists():
            # Fallback to default template path
            template_path = Path(__file__).parent.parent / "resume_templates" / "master_resume.tex"
        
        # Generate LaTeX resume using template
        pdf_path = generate_latex_resume_from_template(enhanced_content, str(template_path), str(output_path))
        
        logger.info(f"Enhanced LaTeX resume generated at {pdf_path}")
        return pdf_path
        
    except Exception as e:
        logger.error(f"Error generating enhanced LaTeX resume: {e}", exc_info=True)
        raise
