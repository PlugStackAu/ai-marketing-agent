# Claude API Configuration (Required)
ANTHROPIC_API_KEY=your_claude_api_key_here

# Server Configuration (Optional)
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Airtable Integration (Optional - for future use)
AIRTABLE_API_KEY=your_airtable_key_here
AIRTABLE_BASE_ID=your_airtable_base_id_here

# Agent Configuration (Optional)
AGENT_MODEL=claude-3-sonnet-20241022
AGENT_MAX_TOKENS=2000
AGENT_TEMPERATURE=0.7

# Logging Configuration (Optional)
LOG_LEVEL=INFO
LOG_FORMAT=json
ENABLE_AUDIT_LOGS=true

# Memory Storage Configuration (Optional)
MEMORY_STORE_TYPE=in_memory
# Future options: sqlite, postgresql
MEMORY_STORE_PATH=./agent_memory.db

# Security Configuration (Optional)
API_KEY_HEADER=X-API-Key
CORS_ORIGINS=*
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600