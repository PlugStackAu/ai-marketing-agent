"""
FastAPI backend server for Claude-powered AI Marketing Agent
with Model Context Protocol (MCP) style architecture
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime
from typing import Optional

from claude_agent import CampaignAgent
from schemas import (
    CampaignBrief, 
    AgentResponse, 
    MemoryContext,
    AgentMemoryStore,
    MockBriefRequest
)

# Initialize FastAPI app
app = FastAPI(
    title="AI Marketing Agent API",
    description="Claude-powered campaign manager with MCP architecture",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Claude agent
agent = CampaignAgent()

# In-memory storage for agent contexts (will expand to SQLite later)
memory_store = AgentMemoryStore()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "AI Marketing Agent API is running",
        "timestamp": datetime.now().isoformat(),
        "agent_role": "Campaign Manager"
    }

@app.post("/campaign/process", response_model=AgentResponse)
async def process_campaign(brief: CampaignBrief):
    """
    Main endpoint: Process a campaign brief and generate marketing assets
    
    This endpoint:
    1. Receives a campaign brief (from Airtable or manual input)
    2. Calls Claude agent to generate strategy and assets
    3. Stores context in memory for future reference
    4. Returns structured marketing assets
    """
    try:
        # Generate campaign assets using Claude
        response = await agent.process_campaign_brief(brief)
        
        # Store the context in memory for future retrieval
        context_id = f"campaign_{brief.campaign_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        memory_context = MemoryContext(
            context_id=context_id,
            agent_role="Campaign Manager",
            input_data=brief.dict(),
            conversation_history=[{
                "timestamp": datetime.now().isoformat(),
                "action": "process_campaign",
                "input": brief.dict(),
                "output": response.dict()
            }],
            output_memory={
                "latest_strategy": response.strategy_summary,
                "latest_post": response.post_text,
                "latest_email": response.email_copy,
                "latest_image_prompt": response.image_prompt
            },
            reasoning_log=[response.agent_notes],
            status="draft",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Store in memory
        memory_store.store_context(context_id, memory_context)
        
        # Add context_id to response
        response.context_id = context_id
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

@app.post("/mock/brief", response_model=dict)
async def create_mock_brief(request: MockBriefRequest):
    """
    Create a mock campaign brief for testing
    Simulates data that would come from Airtable
    """
    try:
        # Load mock data template
        with open("mock_data.json", "r") as f:
            mock_templates = json.load(f)
        
        # Get template based on campaign type
        template = mock_templates.get(request.campaign_type, mock_templates["product_launch"])
        
        # Customize with provided company name
        if request.company_name:
            template["company_name"] = request.company_name
            template["brand_name"] = request.company_name
        
        # Update campaign ID and timestamps
        template["campaign_id"] = f"mock_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        template["created_date"] = datetime.now().isoformat()
        template["deadline"] = datetime.now().replace(day=datetime.now().day + 14).isoformat()
        
        return {"status": "success", "brief": template}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mock brief creation failed: {str(e)}")

@app.get("/memory/{context_id}", response_model=MemoryContext)
async def get_context(context_id: str):
    """
    Retrieve stored agent context by ID
    Useful for reviewing past campaigns and continuing conversations
    """
    context = memory_store.get_context(context_id)
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    return context

@app.get("/memory", response_model=dict)
async def list_contexts(limit: int = 10):
    """
    List all stored contexts with pagination
    Returns summary information for dashboard views
    """
    contexts = memory_store.list_contexts(limit=limit)
    
    # Return summary information
    summaries = []
    for context in contexts:
        summaries.append({
            "context_id": context.context_id,
            "agent_role": context.agent_role,
            "status": context.status,
            "created_at": context.created_at.isoformat(),
            "campaign_info": {
                "campaign_id": context.input_data.get("campaign_id"),
                "company_name": context.input_data.get("company_name"),
                "campaign_type": context.input_data.get("campaign_type")
            }
        })
    
    return {
        "total_contexts": len(summaries),
        "contexts": summaries
    }

@app.put("/memory/{context_id}/status")
async def update_context_status(context_id: str, new_status: str):
    """
    Update the status of a campaign context
    Supports workflow: draft -> in_review -> approved -> published
    """
    valid_statuses = ["draft", "in_review", "approved", "published"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    success = memory_store.update_status(context_id, new_status)
    if not success:
        raise HTTPException(status_code=404, detail="Context not found")
    
    return {"status": "success", "context_id": context_id, "new_status": new_status}

@app.delete("/memory/{context_id}")
async def delete_context(context_id: str):
    """
    Delete a stored context
    Use with caution - this removes all campaign history
    """
    success = memory_store.delete_context(context_id)
    if not success:
        raise HTTPException(status_code=404, detail="Context not found")
    
    return {"status": "success", "message": "Context deleted"}

@app.get("/agent/stats")
async def get_agent_stats():
    """
    Get agent statistics and health information
    """
    contexts = memory_store.list_contexts()
    
    # Calculate statistics
    status_counts = {}
    campaign_types = {}
    
    for context in contexts:
        # Count by status
        status = context.status
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count by campaign type
        campaign_type = context.input_data.get("campaign_type", "unknown")
        campaign_types[campaign_type] = campaign_types.get(campaign_type, 0) + 1
    
    return {
        "total_campaigns": len(contexts),
        "status_breakdown": status_counts,
        "campaign_types": campaign_types,
        "agent_role": "Campaign Manager",
        "memory_store_health": "operational"
    }

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=int(os.environ.get("PORT", 8000)), 
        log_level="info"
    )

# For Vercel deployment
app = app
