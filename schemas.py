"""
Pydantic models for the AI Marketing Agent API
Defines all input/output schemas with validation
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator


class CampaignBrief(BaseModel):
    """
    Campaign brief input schema
    Represents data that would typically come from Airtable
    """
    campaign_id: str = Field(..., description="Unique campaign identifier")
    company_name: str = Field(..., description="Name of the company/client")
    brand_name: str = Field(..., description="Brand name (may differ from company)")
    campaign_type: str = Field(..., description="Type of campaign (e.g., product_launch, awareness, conversion)")
    
    # Campaign objectives and messaging
    objective: str = Field(..., description="Primary campaign objective")
    target_audience: str = Field(..., description="Target audience description")
    key_message: str = Field(..., description="Core message to communicate")
    
    # Brand guidelines
    brand_voice: str = Field(..., description="Brand voice/tone (e.g., professional, casual, playful)")
    brand_values: str = Field(..., description="Key brand values to reflect")
    
    # Campaign constraints
    budget: str = Field(..., description="Campaign budget range or amount")
    platforms: Optional[List[str]] = Field(default=[], description="Target platforms (social, email, web)")
    deadline: str = Field(..., description="Campaign deadline (ISO format)")
    
    # Metadata
    created_date: str = Field(..., description="When brief was created (ISO format)")
    additional_notes: Optional[str] = Field(default=None, description="Any additional context or requirements")
    
    # Airtable-specific fields (optional)
    airtable_record_id: Optional[str] = Field(default=None, description="Airtable record ID if applicable")
    assigned_to: Optional[str] = Field(default=None, description="Team member assigned")
    priority: Optional[str] = Field(default="medium", description="Campaign priority (high, medium, low)")

    @validator('campaign_type')
    def validate_campaign_type(cls, v):
        """Validate campaign type against allowed values"""
        allowed_types = [
            'product_launch', 'brand_awareness', 'lead_generation', 
            'conversion', 'retention', 'event_promotion', 'content_marketing'
        ]
        if v not in allowed_types:
            # Allow any string but log it
            return v
        return v

    @validator('brand_voice')
    def validate_brand_voice(cls, v):
        """Ensure brand voice is descriptive"""
        if len(v.strip()) < 3:
            raise ValueError('Brand voice must be at least 3 characters')
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "campaign_id": "CAMP_2024_001",
                "company_name": "TechStart Inc",
                "brand_name": "TechStart",
                "campaign_type": "product_launch",
                "objective": "Launch new SaaS product to tech professionals",
                "target_audience": "Software developers and tech leads aged 25-45",
                "key_message": "Revolutionary development tools that save 50% of coding time",
                "brand_voice": "Professional yet approachable, technical but not jargony",
                "brand_values": "Innovation, efficiency, developer-first mindset",
                "budget": "$50,000 - $75,000",
                "platforms": ["LinkedIn", "Twitter", "Email", "Developer blogs"],
                "deadline": "2024-12-15T23:59:59Z",
                "created_date": "2024-11-01T10:00:00Z",
                "additional_notes": "Focus on developer pain points and time-saving benefits"
            }
        }


class EmailCopy(BaseModel):
    """Email copy structure"""
    subject_line: str = Field(..., description="Email subject line")
    body_text: str = Field(..., description="Email body content")


class AgentResponse(BaseModel):
    """
    Response schema from the Campaign Manager agent
    Contains all generated marketing assets
    """
    campaign_id: str = Field(..., description="Campaign ID from the brief")
    context_id: Optional[str] = Field(default=None, description="Memory context ID for this response")
    
    # Generated assets
    strategy_summary: str = Field(..., description="Strategic overview and approach")
    post_text: str = Field(..., description="Social media post content")
    email_copy: EmailCopy = Field(..., description="Email campaign copy")
    image_prompt: str = Field(..., description="Detailed prompt for image generation")
    
    # Agent metadata
    agent_notes: str = Field(..., description="Agent reasoning and recommendations")
    generated_at: datetime = Field(default_factory=datetime.now, description="When response was generated")
    
    # Quality metrics (for future use)
    confidence_score: Optional[float] = Field(default=None, description="Agent confidence in response (0-1)")
    
    class Config:
        schema_extra = {
            "example": {
                "campaign_id": "CAMP_2024_001",
                "context_id": "campaign_CAMP_2024_001_20241101_140500",
                "strategy_summary": "This product launch targets developer pain points...",
                "post_text": "🚀 Tired of repetitive coding? Our new dev tools cut coding time in half! Perfect for busy developers who want to focus on innovation, not boilerplate. #DevTools #Productivity",
                "email_copy": {
                    "subject_line": "Cut Your Coding Time in Half (Seriously)",
                    "body_text": "Hi Developer,\n\nWhat if you could finish your sprints early...",
                },
                "image_prompt": "Modern software development workspace, clean desk with dual monitors showing code, developer working efficiently, tech company branding, blue and white color scheme, professional lighting",
                "agent_notes": "Focused on time-saving benefits as primary value prop. Recommended A/B testing subject lines. Consider developer testimonials for social proof.",
                "generated_at": "2024-11-01T14:05:00Z"
            }
        }


class MemoryContext(BaseModel):
    """
    MCP-style memory context for storing agent state and history
    """
    context_id: str = Field(..., description="Unique context identifier")
    agent_role: str = Field(..., description="Role of the agent (e.g., Campaign Manager)")
    
    # Context data
    input_data: Dict[str, Any] = Field(..., description="Original input data (campaign brief)")
    conversation_history: List[Dict[str, Any]] = Field(default=[], description="History of interactions")
    output_memory: Dict[str, Any] = Field(default={}, description="Generated assets and outputs")
    reasoning_log: List[str] = Field(default=[], description="Agent reasoning and decision notes")
    
    # Status tracking
    status: str = Field(default="draft", description="Current status (draft, in_review, approved, published)")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Optional workflow metadata
    assigned_to: Optional[str] = Field(default=None, description="Person/team assigned")
    reviewed_by: Optional[str] = Field(default=None, description="Who reviewed this")
    approval_notes: Optional[str] = Field(default=None, description="Approval/rejection notes")

    @validator('status')
    def validate_status(cls, v):
        """Validate status against workflow states"""
        allowed_statuses = ['draft', 'in_review', 'approved', 'published', 'archived']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {allowed_statuses}')
        return v

    class Config:
        schema_extra = {
            "example": {
                "context_id": "campaign_CAMP_2024_001_20241101_140500",
                "agent_role": "Campaign Manager",
                "input_data": {"campaign_id": "CAMP_2024_001", "company_name": "TechStart Inc"},
                "conversation_history": [
                    {
                        "timestamp": "2024-11-01T14:05:00Z",
                        "action": "process_campaign",
                        "input": "campaign_brief",
                        "output": "marketing_assets"
                    }
                ],
                "output_memory": {
                    "latest_strategy": "Strategic summary...",
                    "latest_post": "Social media post...",
                    "latest_email": "Email copy...",
                    "latest_image_prompt": "Image prompt..."
                },
                "reasoning_log": [
                    "Analyzed target audience demographics",
                    "Identified key pain points in developer workflow",
                    "Optimized messaging for technical audience"
                ],
                "status": "draft",
                "created_at": "2024-11-01T14:05:00Z",
                "updated_at": "2024-11-01T14:05:00Z"
            }
        }


class AgentMemoryStore:
    """
    In-memory storage for agent contexts
    Will be replaced with SQLite or proper database later
    """
    
    def __init__(self):
        self.contexts: Dict[str, MemoryContext] = {}
    
    def store_context(self, context_id: str, context: MemoryContext) -> bool:
        """Store a context in memory"""
        try:
            self.contexts[context_id] = context
            return True
        except Exception:
            return False
    
    def get_context(self, context_id: str) -> Optional[MemoryContext]:
        """Retrieve a context by ID"""
        return self.contexts.get(context_id)
    
    def list_contexts(self, limit: int =