from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from services.llm_service import get_llm

llm = get_llm()


class HiringPostDetails(BaseModel):
    company: str
    role: str
    skills: List[str]
    experience: str
    email: Optional[str] = None
    location: Optional[str] = None
    description: str

    model_config = ConfigDict(arbitrary_types_allowed=True)


parser = PydanticOutputParser(pydantic_object=HiringPostDetails)

post_prompt = PromptTemplate.from_template("""
You are an expert at extracting job information from social media hiring posts.

HIRING POST:
{post_content}

Extract the following information:
1. Company Name
2. Job Role/Position
3. Required Skills (as a list)
4. Experience Required
5. Recruiter Email (if mentioned)
6. Location (if mentioned)
7. Full job description (reconstruct from the post)

IMPORTANT:
- If the post is very brief, infer reasonable details where possible
- If email is not mentioned, leave it empty
- Reconstruct a proper job description from the post content
- Extract all mentioned skills

Return ONLY valid JSON.

{format_instructions}
""")


def parse_hiring_post(post_content):
    """
    Parse a social media hiring post to extract job details.
    
    Args:
        post_content: Text content of the hiring post
    
    Returns:
        HiringPostDetails object with extracted information
    """
    try:
        prompt = post_prompt.format(
            post_content=post_content,
            format_instructions=parser.get_format_instructions()
        )
        
        response = llm.invoke(prompt)
        parsed_output = parser.parse(response.content)
        
        return parsed_output
    except Exception as e:
        print(f"Error parsing hiring post: {e}")
        # Return default values on error
        return HiringPostDetails(
            company="Unknown",
            role="Unknown",
            skills=[],
            experience="Unknown",
            email=None,
            location=None,
            description=post_content
        )
