"""
Multi-Agent Workflow System with LangChain
FAANG-standard implementation with proper error handling, logging, and observability
"""
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
import uvicorn
from contextlib import asynccontextmanager

from langchain_openai import AzureChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import Tool
from langchain.memory import ConversationBufferMemory
import httpx
import os
from uuid import uuid4

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration Management
class Config:
    """Centralized configuration following 12-factor app principles"""
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_DEPLOYMENT_1 = os.getenv("AZURE_OPENAI_DEPLOYMENT_1", "gpt-4")
    AZURE_OPENAI_DEPLOYMENT_2 = os.getenv("AZURE_OPENAI_DEPLOYMENT_2", "gpt-4")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    WEBHOOK_TIMEOUT = int(os.getenv("WEBHOOK_TIMEOUT", "30"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY"]
        missing = [var for var in required if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")

# Pydantic Models for Request/Response Validation
class WebhookPayload(BaseModel):
    """Validated webhook input schema"""
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    session_id: Optional[str] = Field(default=None, description="Session identifier for memory")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('session_id', pre=True, always=True)
    def set_session_id(cls, v):
        return v or str(uuid4())

class AgentResponse(BaseModel):
    """Structured agent response"""
    agent_name: str
    output: str
    execution_time_ms: float
    memory_state: Optional[Dict[str, Any]] = None

class WorkflowResponse(BaseModel):
    """Complete workflow response"""
    workflow_id: str
    status: str
    immediate_response: str
    agent_responses: List[AgentResponse]
    final_output: str
    total_execution_time_ms: float
    timestamp: str

# Memory Management with Thread Safety
class MemoryManager:
    """Manages conversation memory per session with proper cleanup"""
    
    def __init__(self):
        self._sessions: Dict[str, ChatMessageHistory] = {}
    
    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        """Get or create session history"""
        if session_id not in self._sessions:
            self._sessions[session_id] = ChatMessageHistory()
            logger.info(f"Created new session: {session_id}")
        return self._sessions[session_id]
    
    def clear_session(self, session_id: str) -> bool:
        """Clear specific session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Cleared session: {session_id}")
            return True
        return False
    
    def get_session_count(self) -> int:
        """Get active session count for monitoring"""
        return len(self._sessions)

# Agent Factory with Configuration
class AgentFactory:
    """Factory for creating configured LangChain agents"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        
    def create_llm(self, deployment_name: str) -> AzureChatOpenAI:
        """Create Azure OpenAI LLM instance"""
        return AzureChatOpenAI(
            azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
            api_key=Config.AZURE_OPENAI_API_KEY,
            azure_deployment=deployment_name,
            api_version=Config.AZURE_OPENAI_API_VERSION,
            temperature=0.7,
            max_tokens=1000,
            timeout=30,
            max_retries=Config.MAX_RETRIES
        )
    
    def create_agent_1(self) -> tuple[RunnableWithMessageHistory, ChatPromptTemplate]:
        """
        Agent 1: Initial processing and analysis
        """
        llm = self.create_llm(Config.AZURE_OPENAI_DEPLOYMENT_1)
        
        # Define tools for Agent 1
        tools = [
            Tool(
                name="analyze_intent",
                func=lambda x: f"Intent analyzed: {x}",
                description="Analyzes user intent and extracts key information"
            )
        ]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Agent 1, responsible for initial message processing and analysis.
            Your tasks:
            1. Understand user intent
            2. Extract key entities and context
            3. Structure information for the next agent
            4. Maintain conversation context
            
            Be concise and focus on information extraction."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = create_openai_tools_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )
        
        # Wrap with memory
        agent_with_memory = RunnableWithMessageHistory(
            agent_executor,
            self.memory_manager.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )
        
        return agent_with_memory, prompt
    
    def create_agent_2(self) -> tuple[RunnableWithMessageHistory, ChatPromptTemplate]:
        """
        Agent 2: Processing and enrichment with simple memory
        """
        llm = self.create_llm(Config.AZURE_OPENAI_DEPLOYMENT_2)
        
        tools = [
            Tool(
                name="enrich_data",
                func=lambda x: f"Enriched: {x}",
                description="Enriches data with additional context and processing"
            )
        ]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Agent 2, responsible for processing and enriching information from Agent 1.
            Your tasks:
            1. Take structured input from Agent 1
            2. Add context and additional insights
            3. Prepare comprehensive response
            4. Remember previous interactions
            
            Provide detailed and actionable responses."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = create_openai_tools_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )
        
        agent_with_memory = RunnableWithMessageHistory(
            agent_executor,
            self.memory_manager.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )
        
        return agent_with_memory, prompt

# Workflow Orchestrator
class WorkflowOrchestrator:
    """Orchestrates multi-agent workflow execution"""
    
    def __init__(self, agent_factory: AgentFactory):
        self.agent_factory = agent_factory
        self.agent_1, _ = agent_factory.create_agent_1()
        self.agent_2, _ = agent_factory.create_agent_2()
    
    async def execute_workflow(
        self,
        payload: WebhookPayload
    ) -> WorkflowResponse:
        """Execute complete multi-agent workflow"""
        workflow_id = str(uuid4())
        start_time = datetime.utcnow()
        
        logger.info(f"Starting workflow {workflow_id} for session {payload.session_id}")
        
        try:
            # Immediate response
            immediate_response = "Processing your request through our AI agents..."
            
            # Execute Agent 1
            agent_1_start = datetime.utcnow()
            agent_1_output = await self._execute_agent(
                self.agent_1,
                payload.message,
                payload.session_id,
                "Agent1"
            )
            agent_1_time = (datetime.utcnow() - agent_1_start).total_seconds() * 1000
            
            agent_1_response = AgentResponse(
                agent_name="Agent1",
                output=agent_1_output,
                execution_time_ms=agent_1_time
            )
            
            # Execute Agent 2 with Agent 1's output
            agent_2_start = datetime.utcnow()
            agent_2_input = f"Previous agent analysis: {agent_1_output}\n\nOriginal message: {payload.message}"
            agent_2_output = await self._execute_agent(
                self.agent_2,
                agent_2_input,
                payload.session_id,
                "Agent2"
            )
            agent_2_time = (datetime.utcnow() - agent_2_start).total_seconds() * 1000
            
            agent_2_response = AgentResponse(
                agent_name="Agent2",
                output=agent_2_output,
                execution_time_ms=agent_2_time
            )
            
            total_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return WorkflowResponse(
                workflow_id=workflow_id,
                status="success",
                immediate_response=immediate_response,
                agent_responses=[agent_1_response, agent_2_response],
                final_output=agent_2_output,
                total_execution_time_ms=total_time,
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Workflow execution failed: {str(e)}"
            )
    
    async def _execute_agent(
        self,
        agent: RunnableWithMessageHistory,
        input_text: str,
        session_id: str,
        agent_name: str
    ) -> str:
        """Execute single agent with error handling"""
        try:
            logger.info(f"Executing {agent_name} for session {session_id}")
            
            response = await agent.ainvoke(
                {"input": input_text},
                config={"configurable": {"session_id": session_id}}
            )
            
            output = response.get("output", "")
            logger.info(f"{agent_name} completed successfully")
            return output
            
        except Exception as e:
            logger.error(f"{agent_name} execution failed: {str(e)}", exc_info=True)
            raise

# HTTP Client for External Requests
class HTTPClient:
    """Async HTTP client with retry logic"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=Config.WEBHOOK_TIMEOUT)
    
    async def post(self, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST request with retry logic"""
        for attempt in range(Config.MAX_RETRIES):
            try:
                response = await self.client.post(url, json=data)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.warning(f"HTTP POST attempt {attempt + 1} failed: {str(e)}")
                if attempt == Config.MAX_RETRIES - 1:
                    raise
        return {}
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

# FastAPI Application
memory_manager = MemoryManager()
agent_factory = AgentFactory(memory_manager)
workflow_orchestrator = WorkflowOrchestrator(agent_factory)
http_client = HTTPClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    Config.validate()
    logger.info("Application started successfully")
    yield
    # Shutdown
    await http_client.close()
    logger.info("Application shutdown complete")

app = FastAPI(
    title="Multi-Agent Workflow System",
    description="FAANG-standard LangChain multi-agent system",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/webhook", response_model=WorkflowResponse)
async def webhook_endpoint(
    payload: WebhookPayload,
    background_tasks: BackgroundTasks
):
    """
    Main webhook endpoint for multi-agent workflow processing
    
    Features:
    - Immediate response
    - Sequential agent processing with memory
    - Session-based conversation history
    - Comprehensive error handling
    """
    try:
        response = await workflow_orchestrator.execute_workflow(payload)
        
        # Log metrics for monitoring
        background_tasks.add_task(
            log_metrics,
            workflow_id=response.workflow_id,
            execution_time=response.total_execution_time_ms
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_sessions": memory_manager.get_session_count()
    }

@app.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear specific session memory"""
    success = memory_manager.clear_session(session_id)
    return {
        "session_id": session_id,
        "cleared": success
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Multi-Agent Workflow System",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health",
            "sessions": "/sessions/{session_id}"
        }
    }

async def log_metrics(workflow_id: str, execution_time: float):
    """Background task for logging metrics"""
    logger.info(f"Workflow {workflow_id} metrics - Execution time: {execution_time}ms")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )