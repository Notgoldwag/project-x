"""
Enhanced Multi-Agent Workflow System with N8N-Style Engine Integration
Combines FastAPI with dynamic workflow configuration
"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
import uvicorn
import json
import os
from contextlib import asynccontextmanager

# Import our n8n-style workflow engine
from n8n_workflow_engine import (
    WorkflowEngine, 
    WorkflowDefinition, 
    NodeConfig, 
    Connection,
    NodeType,
    create_n8n_workflow_example,
    create_prompt_engineering_workflow  # New import for your specific workflow
)

# Import Azure OpenAI components
from langchain_openai import AzureChatOpenAI
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    AZURE_OPENAI_DEPLOYMENT_1 = os.getenv("AZURE_OPENAI_DEPLOYMENT_1", "gpt-4")
    AZURE_OPENAI_DEPLOYMENT_2 = os.getenv("AZURE_OPENAI_DEPLOYMENT_2", "gpt-4")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

# Pydantic Models
class WorkflowRequest(BaseModel):
    """Input for workflow execution"""
    message: str = Field(..., min_length=1, description="User message")
    session_id: Optional[str] = Field(default=None, description="Session ID for memory")
    workflow_id: Optional[str] = Field(default=None, description="Specific workflow to use")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class WorkflowDefinitionRequest(BaseModel):
    """Request to create/update workflow definition"""
    name: str
    nodes: List[Dict[str, Any]]
    connections: List[Dict[str, str]]
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)

class WorkflowResponse(BaseModel):
    """Response from workflow execution"""
    workflow_id: str
    session_id: str
    status: str
    immediate_response: str
    final_output: Any
    execution_history: List[Dict[str, Any]]
    total_execution_time_ms: float
    timestamp: str

# LLM Factory for Azure OpenAI
def create_azure_llm(model_config: Dict[str, Any] = None) -> AzureChatOpenAI:
    """Create Azure OpenAI LLM instance"""
    config = model_config or {}
    
    # Check if we have Azure configuration
    if Config.AZURE_OPENAI_ENDPOINT:
        return AzureChatOpenAI(
            azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
            api_key=Config.AZURE_OPENAI_API_KEY,
            azure_deployment=config.get('deployment', Config.AZURE_OPENAI_DEPLOYMENT_1),
            api_version=Config.AZURE_OPENAI_API_VERSION,
            temperature=config.get('temperature', 0.7),
            max_tokens=config.get('max_tokens', 1000),
            timeout=30,
            max_retries=3
        )
    else:
        # Fallback to standard OpenAI
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=config.get('deployment', 'gpt-4o-mini'),
            temperature=config.get('temperature', 0.7),
            max_tokens=config.get('max_tokens', 1000),
            timeout=30,
            max_retries=3
        )

# Global workflow engine
workflow_engine = WorkflowEngine(llm_factory=create_azure_llm)

# Replace the process_prompt_engineering_sync function with actual LangChain implementation
def process_prompt_engineering_sync(message: str, session_id: str = None) -> Dict[str, Any]:
    """
    Synchronous wrapper for the three-agent orchestration.
    This implements the actual 3-agent LangChain pipeline.
    
    Agent 1 (Prompt Architect): Creates initial prompt structure
    Agent 2 (Guardrail Engineer): Adds safety and quality checks  
    Agent 3 (Template Polisher): Final optimization and formatting
    """
    import time
    from uuid import uuid4
    
    start_time = time.time()
    session_id = session_id or str(uuid4())
    workflow_id = f"prompt_eng_{int(start_time)}"
    
    try:
        # Create the LLM instance
        llm = create_azure_llm({
            'temperature': 0.7,
            'max_tokens': 2000
        })
        
        execution_history = []
        
        # Agent 1: Prompt Architect
        architect_prompt = f"""You are a Prompt Architect specializing in creating high-quality system prompts.
        
Your task: Transform the user's request into a well-structured prompt template.

User Request: {message}

Create a comprehensive prompt template that includes:
1. Clear role definition
2. Specific instructions 
3. Expected output format
4. Context and constraints
5. Example interactions (if applicable)

Focus on clarity, specificity, and professional tone. This will be refined by subsequent agents."""

        architect_start = time.time()
        architect_response = llm.invoke(architect_prompt)
        architect_result = architect_response.content
        architect_time = (time.time() - architect_start) * 1000
        
        execution_history.append({
            "agent": "Prompt Architect",
            "execution_time_ms": architect_time,
            "input": message,
            "output": architect_result[:200] + "..." if len(architect_result) > 200 else architect_result,
            "status": "completed"
        })
        
        # Agent 2: Guardrail Engineer  
        guardrail_prompt = f"""You are a Guardrail Engineer responsible for prompt safety and quality assurance.

Review this prompt template created by the Prompt Architect:

{architect_result}

Your tasks:
1. Add safety guardrails and ethical boundaries
2. Include handling for edge cases and errors
3. Add quality checks and validation steps
4. Ensure prompt prevents harmful or inappropriate outputs
5. Add robustness against prompt injection attacks

Enhance the template while maintaining its core functionality."""

        guardrail_start = time.time()
        guardrail_response = llm.invoke(guardrail_prompt)
        guardrail_result = guardrail_response.content
        guardrail_time = (time.time() - guardrail_start) * 1000
        
        execution_history.append({
            "agent": "Guardrail Engineer", 
            "execution_time_ms": guardrail_time,
            "input": "Enhanced prompt from Architect",
            "output": guardrail_result[:200] + "..." if len(guardrail_result) > 200 else guardrail_result,
            "status": "completed"
        })
        
        # Agent 3: Template Polisher
        polisher_prompt = f"""You are a Template Polisher specializing in final optimization of prompt templates.

Take this safety-enhanced prompt template:

{guardrail_result}

Your final tasks:
1. Optimize for clarity and conciseness
2. Ensure consistent formatting and structure
3. Add professional polish and refinement
4. Create the final production-ready template
5. Include usage instructions and best practices

Deliver a polished, production-ready prompt template that meets MAANG engineering standards."""

        polisher_start = time.time()
        polisher_response = llm.invoke(polisher_prompt)
        final_result = polisher_response.content
        polisher_time = (time.time() - polisher_start) * 1000
        
        execution_history.append({
            "agent": "Template Polisher",
            "execution_time_ms": polisher_time, 
            "input": "Safety-enhanced prompt from Guardrail Engineer",
            "output": final_result[:200] + "..." if len(final_result) > 200 else final_result,
            "status": "completed"
        })
        
        total_time = (time.time() - start_time) * 1000
        
        return {
            "workflow_id": workflow_id,
            "session_id": session_id,
            "status": "completed",
            "immediate_response": "✅ 3-Agent Pipeline Completed Successfully",
            "final_output": {
                "final_prompt_template": final_result,
                "agent_pipeline": [
                    {"agent": "Prompt Architect", "contribution": "Initial structure and clarity"},
                    {"agent": "Guardrail Engineer", "contribution": "Safety and robustness"},
                    {"agent": "Template Polisher", "contribution": "Final optimization"}
                ],
                "metadata": {
                    "original_request": message,
                    "processing_pipeline": "3-Agent MAANG-Grade",
                    "quality_standard": "Production Ready"
                }
            },
            "execution_history": execution_history,
            "total_execution_time_ms": total_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"3-Agent pipeline failed: {str(e)}", exc_info=True)
        
        # Return error response in same format
        return {
            "workflow_id": workflow_id,
            "session_id": session_id,
            "status": "error", 
            "immediate_response": f"❌ Pipeline Error: {str(e)}",
            "final_output": {
                "error": str(e),
                "original_request": message,
                "failed_at": "LangChain execution"
            },
            "execution_history": execution_history,
            "total_execution_time_ms": (time.time() - start_time) * 1000,
            "timestamp": datetime.utcnow().isoformat()
        }

# Workflow storage (in production, use a proper database)
workflow_store: Dict[str, WorkflowDefinition] = {}

# Initialize with default workflows
def initialize_default_workflows():
    """Initialize with default workflows including prompt engineering"""
    # General workflow
    default_workflow = create_n8n_workflow_example()
    workflow_store['default'] = default_workflow
    workflow_store['general'] = default_workflow
    
    # Prompt engineering workflow
    prompt_eng_workflow = create_prompt_engineering_workflow()
    workflow_store['prompt_engineering'] = prompt_eng_workflow
    workflow_store['prompt_eng'] = prompt_eng_workflow  # Short alias
    
    logger.info(f"Initialized default workflow: {default_workflow.workflow_id}")
    logger.info(f"Initialized prompt engineering workflow: {prompt_eng_workflow.workflow_id}")
    logger.info(f"Available workflows: {list(workflow_store.keys())}")

# FastAPI App
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    try:
        initialize_default_workflows()  # Updated function name
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Application shutdown")

app = FastAPI(
    title="N8N-Style Multi-Agent Workflow System",
    description="Dynamic workflow configuration and execution with LangChain agents",
    version="2.0.0",
    lifespan=lifespan
)

# API Endpoints

@app.post("/webhook", response_model=WorkflowResponse)
async def webhook_endpoint(request: WorkflowRequest, background_tasks: BackgroundTasks):
    """
    Main webhook endpoint that executes n8n-style workflows
    
    This endpoint:
    1. Accepts incoming requests
    2. Provides immediate response 
    3. Executes multi-agent workflow
    4. Returns comprehensive results
    """
    try:
        # Get workflow to execute
        workflow_id = request.workflow_id or 'default'
        workflow = workflow_store.get(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=404, 
                detail=f"Workflow {workflow_id} not found"
            )
        
        logger.info(f"Executing workflow {workflow_id} for session {request.session_id}")
        
        # Execute workflow
        result = await workflow_engine.execute_workflow(
            workflow,
            {
                'message': request.message,
                'metadata': request.metadata
            },
            session_id=request.session_id
        )
        
        # Get immediate response from workflow results
        immediate_response = "Processing your request through our AI agents..."
        if result.get('execution_history'):
            first_result = result['execution_history'][0]
            if 'immediate_response' in str(first_result):
                immediate_response = "Request received and processing started"
        
        # Format response
        response = WorkflowResponse(
            workflow_id=result['workflow_id'],
            session_id=result['session_id'],
            status=result['status'],
            immediate_response=immediate_response,
            final_output=result['final_output'],
            execution_history=result['execution_history'],
            total_execution_time_ms=result['total_execution_time_ms'],
            timestamp=result['timestamp']
        )
        
        # Log metrics in background
        background_tasks.add_task(
            log_workflow_metrics,
            workflow_id=result['workflow_id'],
            execution_time=result['total_execution_time_ms']
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Webhook execution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/prompt-engineering", response_model=WorkflowResponse)
async def prompt_engineering_endpoint(
    request: WorkflowRequest,
    background_tasks: BackgroundTasks
):
    """
    Specialized endpoint for MAANG-grade prompt engineering workflow
    
    This endpoint processes requests through a 3-agent pipeline:
    1. Agent 1 (Prompt Architect): Creates initial prompt template
    2. Agent 2 (Guardrail Engineer): Refines and audits the template  
    3. Agent 3 (Template Polisher): Final polishing and standardization
    """
    try:
        # Force use of prompt engineering workflow
        request.workflow_id = 'prompt_engineering'
        
        logger.info(f"Executing prompt engineering workflow for session {request.session_id}")
        
        # Get the prompt engineering workflow
        workflow = workflow_store.get('prompt_engineering')
        if not workflow:
            raise HTTPException(
                status_code=500, 
                detail="Prompt engineering workflow not configured"
            )
        
        # Execute workflow
        result = await workflow_engine.execute_workflow(
            workflow,
            {
                'message': request.message,
                'metadata': {
                    **request.metadata,
                    'workflow_type': 'prompt_engineering',
                    'quality_standard': 'MAANG'
                }
            },
            session_id=request.session_id
        )
        
        # Specialized immediate response for prompt engineering
        immediate_response = "Processing your prompt engineering request through our 3-agent MAANG-grade pipeline..."
        
        # Format response
        response = WorkflowResponse(
            workflow_id=result['workflow_id'],
            session_id=result['session_id'], 
            status=result['status'],
            immediate_response=immediate_response,
            final_output=result['final_output'],
            execution_history=result['execution_history'],
            total_execution_time_ms=result['total_execution_time_ms'],
            timestamp=result['timestamp']
        )
        
        # Log metrics
        background_tasks.add_task(
            log_workflow_metrics,
            workflow_id=result['workflow_id'],
            execution_time=result['total_execution_time_ms'],
            workflow_type="prompt_engineering"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Prompt engineering workflow failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workflows")
async def create_workflow(workflow_def: WorkflowDefinitionRequest):
    """Create or update a workflow definition"""
    try:
        # Convert to internal format
        nodes = []
        for node_data in workflow_def.nodes:
            node_config = NodeConfig(
                node_id=node_data['node_id'],
                node_type=NodeType(node_data['node_type']),
                name=node_data['name'],
                config=node_data.get('config', {}),
                position=node_data.get('position', {})
            )
            nodes.append(node_config)
        
        connections = []
        for conn_data in workflow_def.connections:
            connection = Connection(
                source_node=conn_data['source_node'],
                target_node=conn_data['target_node'],
                condition=conn_data.get('condition'),
                output_key=conn_data.get('output_key')
            )
            connections.append(connection)
        
        # Create workflow definition
        workflow = WorkflowDefinition(
            workflow_id=str(len(workflow_store) + 1),  # Simple ID generation
            name=workflow_def.name,
            nodes=nodes,
            connections=connections,
            settings=workflow_def.settings
        )
        
        # Store workflow
        workflow_store[workflow.workflow_id] = workflow
        
        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "status": "created",
            "node_count": len(nodes),
            "connection_count": len(connections)
        }
        
    except Exception as e:
        logger.error(f"Workflow creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/workflows")
async def list_workflows():
    """List all available workflows"""
    workflows = []
    for workflow_id, workflow in workflow_store.items():
        if workflow_id != 'default':  # Skip the default alias
            workflows.append({
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "node_count": len(workflow.nodes),
                "connection_count": len(workflow.connections)
            })
    
    return {"workflows": workflows, "count": len(workflows)}

@app.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get specific workflow definition"""
    workflow = workflow_store.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return {
        "workflow_id": workflow.workflow_id,
        "name": workflow.name,
        "nodes": [
            {
                "node_id": node.node_id,
                "node_type": node.node_type.value,
                "name": node.name,
                "config": node.config,
                "position": node.position
            }
            for node in workflow.nodes
        ],
        "connections": [
            {
                "source_node": conn.source_node,
                "target_node": conn.target_node,
                "condition": conn.condition,
                "output_key": conn.output_key
            }
            for conn in workflow.connections
        ],
        "settings": workflow.settings
    }

@app.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow"""
    if workflow_id == 'default':
        raise HTTPException(status_code=400, detail="Cannot delete default workflow")
    
    if workflow_id not in workflow_store:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    del workflow_store[workflow_id]
    return {"workflow_id": workflow_id, "status": "deleted"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "workflow_count": len([k for k in workflow_store.keys() if k != 'default']),
        "azure_configured": bool(Config.AZURE_OPENAI_ENDPOINT),
        "version": "2.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint with API documentation"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>N8N-Style Multi-Agent Workflow System</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .endpoint { margin: 20px 0; padding: 10px; background: #f0f0f0; border-radius: 5px; }
            .method { font-weight: bold; color: #007acc; }
            code { background: #e8e8e8; padding: 2px 4px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>🚀 N8N-Style Multi-Agent Workflow System</h1>
        <p>Dynamic workflow configuration and execution with LangChain agents</p>
        
        <h2>📋 Available Endpoints:</h2>
        
        <div class="endpoint">
            <span class="method">POST</span> <code>/webhook</code><br>
            Execute workflow with user input
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span> <code>/prompt-engineering</code><br>
            MAANG-grade prompt engineering workflow (3 agents)
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/workflows</code><br>
            List all available workflows
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span> <code>/workflows</code><br>
            Create new workflow definition
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/workflows/{workflow_id}</code><br>
            Get specific workflow definition
        </div>
        
        <div class="endpoint">
            <span class="method">DELETE</span> <code>/workflows/{workflow_id}</code><br>
            Delete workflow
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/health</code><br>
            Health check and system status
        </div>
        
        <h2>📊 Example Usage:</h2>
        <h3>General Workflow:</h3>
        <pre><code>
curl -X POST "http://localhost:8000/webhook" \\
     -H "Content-Type: application/json" \\
     -d '{
       "message": "I need help with business strategy",
       "session_id": "user123"
     }'
        </code></pre>
        
        <h3>Prompt Engineering Workflow:</h3>
        <pre><code>
curl -X POST "http://localhost:8000/prompt-engineering" \\
     -H "Content-Type: application/json" \\
     -d '{
       "message": "Create a system prompt for a code review AI agent",
       "session_id": "prompt_user123"
     }'
        </code></pre>
        
        <h2>🔧 Features:</h2>
        <ul>
            <li>✅ N8N-style visual workflow support</li>
            <li>✅ Multi-agent sequential processing</li>
            <li>✅ Azure OpenAI integration</li>
            <li>✅ Session-based memory management</li>
            <li>✅ Dynamic workflow configuration</li>
            <li>✅ Immediate response capability</li>
            <li>✅ Comprehensive error handling</li>
            <li>✅ Performance monitoring</li>
        </ul>
    </body>
    </html>
    """)

async def log_workflow_metrics(workflow_id: str, execution_time: float, workflow_type: str = "general"):
    """Background task for logging workflow metrics"""
    logger.info(f"Workflow {workflow_id} ({workflow_type}) metrics - Execution time: {execution_time}ms")

# Example test function
@app.post("/test")
async def test_workflow():
    """Test endpoint for quick workflow verification"""
    test_request = WorkflowRequest(
        message="Test message for multi-agent workflow",
        session_id="test_session"
    )
    
    try:
        response = await webhook_endpoint(test_request, BackgroundTasks())
        return {
            "test_status": "success",
            "response_preview": str(response.final_output)[:200] + "..." if response.final_output else "No output",
            "execution_time_ms": response.total_execution_time_ms
        }
    except Exception as e:
        return {
            "test_status": "failed",
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(
        "main_enhanced:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )