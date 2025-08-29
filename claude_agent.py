"""
Claude Agent implementation with MCP-style context management
Handles all Claude API interactions and reasoning
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import logging

from anthropic import Anthropic
from schemas import CampaignBrief, AgentResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CampaignAgent:
    """
    Campaign Manager Agent powered by Claude
    
    This agent specializes in:
    - Reading campaign briefs
    - Generating marketing strategies
    - Creating social media posts
    - Writing email copy
    - Generating image prompts
    """
    
    def __init__(self):
        """Initialize the Claude client and agent configuration"""
        
        # Initialize Anthropic client
        # Make sure to set ANTHROPIC_API_KEY environment variable
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not found. Using placeholder for development.")
            self.client = None
        else:
            self.client = Anthropic(api_key=api_key)
        
        # Agent configuration
        self.agent_role = "Campaign Manager"
        self.model = "claude-3-sonnet-20241022"  # Using Claude 3 Sonnet
        self.max_tokens = 2000
        
        # System prompt that defines the agent's behavior
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt that defines agent behavior"""
        return """You are an expert Campaign Manager AI agent. Your role is to analyze campaign briefs and generate comprehensive marketing assets.

When given a campaign brief, you must:

1. **Analyze the brief thoroughly** - understand the target audience, goals, brand voice, and constraints
2. **Generate a strategic summary** - key insights and approach
3. **Create a social media post** - engaging, platform-appropriate content
4. **Write email copy** - compelling subject line and body text
5. **Generate an image prompt** - detailed prompt for visual asset creation
6. **Provide agent notes** - your reasoning and recommendations

**Output Format Requirements:**
Always respond with a valid JSON object containing these exact fields:
- strategy_summary: String with 2-3 paragraphs of strategic insights
- post_text: String with social media post (include relevant hashtags)
- email_copy: Object with "subject_line" and "body_text" fields
- image_prompt: String with detailed visual description for image generation
- agent_notes: String with your reasoning, recommendations, and next steps

**Guidelines:**
- Match the brand voice and tone specified in the brief
- Consider the target audience demographics and preferences  
- Ensure all content aligns with campaign objectives
- Be specific and actionable in your recommendations
- Keep social posts under 280 characters unless specified otherwise
- Make email copy compelling and conversion-focused
- Create detailed image prompts that capture brand aesthetics

**Response must be valid JSON only - no additional text or formatting.**"""

    async def process_campaign_brief(self, brief: CampaignBrief) -> AgentResponse:
        """
        Main method: Process a campaign brief and generate marketing assets
        
        Args:
            brief: CampaignBrief object with all campaign information
            
        Returns:
            AgentResponse with generated marketing assets
        """
        try:
            # Build the user message with campaign brief details
            user_message = self._build_user_message(brief)
            
            # Call Claude API
            if self.client is None:
                # Return mock response for development/testing
                logger.info("Using mock response (no API key provided)")
                return self._generate_mock_response(brief)
            
            # Make the actual Claude API call
            response = await self._call_claude_api(user_message)
            
            # Parse and validate the response
            agent_response = self._parse_claude_response(response, brief)
            
            # Log the interaction for audit purposes
            self._log_interaction(brief, agent_response)
            
            return agent_response
            
        except Exception as e:
            logger.error(f"Error processing campaign brief: {str(e)}")
            
            # Return fallback response instead of failing
            return self._generate_fallback_response(brief, str(e))
    
    def _build_user_message(self, brief: CampaignBrief) -> str:
        """Build the user message containing the campaign brief"""
        
        # Convert brief to structured text
        brief_text = f"""
CAMPAIGN BRIEF ANALYSIS REQUEST

Campaign ID: {brief.campaign_id}
Company: {brief.company_name}
Brand: {brief.brand_name}
Campaign Type: {brief.campaign_type}

CAMPAIGN DETAILS:
Objective: {brief.objective}
Target Audience: {brief.target_audience}
Key Message: {brief.key_message}

BRAND GUIDELINES:
Brand Voice: {brief.brand_voice}
Brand Values: {brief.brand_values}

DELIVERABLES NEEDED:
- Strategy Summary
- Social Media Post
- Email Campaign Copy
- Image Generation Prompt

CONSTRAINTS:
Budget: {brief.budget}
Timeline: Campaign created {brief.created_date}, deadline {brief.deadline}
Platform Focus: {', '.join(brief.platforms) if brief.platforms else 'Multi-platform'}

ADDITIONAL CONTEXT:
{brief.additional_notes if brief.additional_notes else 'No additional notes provided'}

Please analyze this brief and generate comprehensive marketing assets following the specified JSON format.
"""
        
        return brief_text.strip()
    
    async def _call_claude_api(self, user_message: str) -> str:
        """Make async call to Claude API"""
        
        try:
            # Create the message
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.7,
                system=self.system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            )
            
            # Extract text content from response
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Claude API call failed: {str(e)}")
            raise
    
    def _parse_claude_response(self, claude_response: str, brief: CampaignBrief) -> AgentResponse:
        """Parse Claude's JSON response into AgentResponse object"""
        
        try:
            # Parse JSON response
            response_data = json.loads(claude_response.strip())
            
            # Validate required fields
            required_fields = ["strategy_summary", "post_text", "email_copy", "image_prompt", "agent_notes"]
            for field in required_fields:
                if field not in response_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create AgentResponse object
            return AgentResponse(
                campaign_id=brief.campaign_id,
                strategy_summary=response_data["strategy_summary"],
                post_text=response_data["post_text"],
                email_copy=response_data["email_copy"],
                image_prompt=response_data["image_prompt"],
                agent_notes=response_data["agent_notes"],
                generated_at=datetime.now()
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {str(e)}")
            logger.error(f"Raw response: {claude_response}")
            raise ValueError("Claude response was not valid JSON")
        
        except Exception as e:
            logger.error(f"Error parsing Claude response: {str(e)}")
            raise
    
    def _generate_mock_response(self, brief: CampaignBrief) -> AgentResponse:
        """Generate a mock response for testing when no API key is available"""
        
        return AgentResponse(
            campaign_id=brief.campaign_id,
            strategy_summary=f"Mock strategy for {brief.company_name}'s {brief.campaign_type} campaign. This is a placeholder response generated without calling Claude API. The strategy focuses on {brief.target_audience} with emphasis on {brief.key_message}.",
            post_text=f"🚀 Exciting news from {brief.company_name}! {brief.key_message} Perfect for {brief.target_audience}. #Innovation #MockPost",
            email_copy={
                "subject_line": f"Don't Miss This: {brief.key_message}",
                "body_text": f"Dear Valued Customer,\n\n{brief.key_message}\n\nThis mock email copy is generated for {brief.company_name}'s {brief.campaign_type} campaign.\n\nBest regards,\nThe {brief.company_name} Team"
            },
            image_prompt=f"Professional marketing image for {brief.company_name}, showing {brief.key_message}, style: modern and clean, colors: brand colors, mood: {brief.brand_voice}, target audience: {brief.target_audience}",
            agent_notes=f"MOCK RESPONSE: This is a placeholder response for testing. In production, this would contain Claude's strategic insights about the {brief.campaign_type} campaign for {brief.company_name}.",
            generated_at=datetime.now()
        )
    
    def _generate_fallback_response(self, brief: CampaignBrief, error_message: str) -> AgentResponse:
        """Generate a fallback response when Claude API fails"""
        
        return AgentResponse(
            campaign_id=brief.campaign_id,
            strategy_summary=f"Error processing campaign brief. The agent encountered an issue but has generated fallback content for {brief.company_name}'s {brief.campaign_type} campaign.",
            post_text=f"Updates coming soon from {brief.company_name}! Stay tuned. #{brief.company_name}",
            email_copy={
                "subject_line": f"Important Update from {brief.company_name}",
                "body_text": f"Hello,\n\nWe're working on something exciting and will share more details soon.\n\nThank you for your patience.\n\n{brief.company_name} Team"
            },
            image_prompt=f"Simple, professional image for {brief.company_name}, clean design, brand colors",
            agent_notes=f"FALLBACK RESPONSE: Agent error - {error_message}. Manual review required.",
            generated_at=datetime.now()
        )
    
    def _log_interaction(self, brief: CampaignBrief, response: AgentResponse):
        """Log the interaction for audit and debugging purposes"""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_role": self.agent_role,
            "campaign_id": brief.campaign_id,
            "company_name": brief.company_name,
            "campaign_type": brief.campaign_type,
            "processing_status": "success",
            "response_generated": True,
            "model_used": self.model
        }
        
        # Write to log file (markdown format for readability)
        log_filename = f"agent_logs_{datetime.now().strftime('%Y%m')}.md"
        
        try:
            with open(log_filename, "a", encoding="utf-8") as f:
                f.write(f"\n## Campaign Processing Log\n")
                f.write(f"**Timestamp:** {log_entry['timestamp']}\n")
                f.write(f"**Campaign ID:** {log_entry['campaign_id']}\n")
                f.write(f"**Company:** {log_entry['company_name']}\n")
                f.write(f"**Type:** {log_entry['campaign_type']}\n")
                f.write(f"**Status:** {log_entry['processing_status']}\n")
                f.write(f"**Model:** {log_entry['model_used']}\n")
                f.write("---\n\n")
                
        except Exception as e:
            logger.error(f"Failed to write log: {str(e)}")

    def get_agent_info(self) -> Dict:
        """Return information about the agent configuration"""
        
        return {
            "agent_role": self.agent_role,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "api_available": self.client is not None,
            "capabilities": [
                "Campaign Strategy Generation",
                "Social Media Content Creation", 
                "Email Copy Writing",
                "Image Prompt Generation",
                "Brand Voice Adaptation"
            ]
        }
