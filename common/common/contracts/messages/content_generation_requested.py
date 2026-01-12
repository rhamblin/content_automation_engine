from dataclasses import dataclass
from typing import Optional, Dict, Any
from ..interfaces.message import IMessage

@dataclass
class ContentGenerationRequested(IMessage):
    """Message contract for content generation requests"""

    job_id: str
    project_id: str
    integration_profile_id: str
    data: Optional[Dict[str, Any]] = None
