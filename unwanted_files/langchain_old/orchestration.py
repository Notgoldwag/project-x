"""
Standalone 3-Agent LangChain Orchestration for Flask Integration
No FastAPI dependencies - pure Python with LangChain only
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, Any
from uuid import uuid4

# Configure logging
logger = logging.getLogger(__name__)

def create_llm(model_config: Dict[str, Any] = None):
    """Create LLM instance - Azure OpenAI or standard OpenAI"""
    config = model_config or {}
    
    # Check for Azure OpenAI configuration
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    if azure_endpoint and azure_key:
        from langchain_openai import AzureChatOpenAI
        return AzureChatOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=azure_key,
            azure_deployment=config.get('deployment', os.getenv("AZURE_OPENAI_DEPLOYMENT_1", "gpt-4")),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            temperature=config.get('temperature', 0.7),
            max_tokens=config.get('max_tokens', 2000),
            timeout=30,
            max_retries=3
        )
    else:
        # Fallback to standard OpenAI
        from langchain_openai import ChatOpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        return ChatOpenAI(
            api_key=openai_key,
            model=config.get('deployment', 'gpt-4o-mini'),
            temperature=config.get('temperature', 0.7),
            max_tokens=config.get('max_tokens', 2000),
            timeout=30,
            max_retries=3
        )


def process_prompt_engineering(message: str, session_id: str = None) -> Dict[str, Any]:
    """
    Three-agent orchestration for MAANG-grade prompt engineering.
    
    Agent 1 (Prompt Architect): Creates initial prompt structure
    Agent 2 (Guardrail Engineer): Adds safety and quality checks  
    Agent 3 (Template Polisher): Final optimization and formatting
    
    Args:
        message: The user's draft prompt request
        session_id: Optional session ID for conversation tracking
    
    Returns:
        Dict with structured response including final_output and execution_history
    """
    start_time = time.time()
    session_id = session_id or str(uuid4())
    workflow_id = f"prompt_eng_{int(start_time)}"
    
    try:
        # Create the LLM instance
        llm = create_llm({
            'temperature': 0.7,
            'max_tokens': 2000
        })
        
        execution_history = []
        
        # ==================== AGENT 1: PROMPT ARCHITECT ====================
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

        logger.info("Agent 1 (Prompt Architect) - Starting...")
        architect_start = time.time()
        architect_response = llm.invoke(architect_prompt)
        architect_result = architect_response.content
        architect_time = (time.time() - architect_start) * 1000
        
        execution_history.append({
            "agent": "Prompt Architect",
            "execution_time_ms": architect_time,
            "input_preview": message[:100] + "..." if len(message) > 100 else message,
            "output_preview": architect_result[:200] + "..." if len(architect_result) > 200 else architect_result,
            "status": "completed"
        })
        logger.info(f"Agent 1 completed in {architect_time:.2f}ms")
        
        # ==================== AGENT 2: GUARDRAIL ENGINEER ====================
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

        logger.info("Agent 2 (Guardrail Engineer) - Starting...")
        guardrail_start = time.time()
        guardrail_response = llm.invoke(guardrail_prompt)
        guardrail_result = guardrail_response.content
        guardrail_time = (time.time() - guardrail_start) * 1000
        
        execution_history.append({
            "agent": "Guardrail Engineer", 
            "execution_time_ms": guardrail_time,
            "input_preview": "Enhanced prompt from Architect",
            "output_preview": guardrail_result[:200] + "..." if len(guardrail_result) > 200 else guardrail_result,
            "status": "completed"
        })
        logger.info(f"Agent 2 completed in {guardrail_time:.2f}ms")
        
        # ==================== AGENT 3: TEMPLATE POLISHER ====================
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

        logger.info("Agent 3 (Template Polisher) - Starting...")
        polisher_start = time.time()
        polisher_response = llm.invoke(polisher_prompt)
        final_result = polisher_response.content
        polisher_time = (time.time() - polisher_start) * 1000
        
        execution_history.append({
            "agent": "Template Polisher",
            "execution_time_ms": polisher_time, 
            "input_preview": "Safety-enhanced prompt from Guardrail Engineer",
            "output_preview": final_result[:200] + "..." if len(final_result) > 200 else final_result,
            "status": "completed"
        })
        logger.info(f"Agent 3 completed in {polisher_time:.2f}ms")
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"✅ 3-Agent pipeline completed successfully in {total_time:.2f}ms")
        
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
        logger.error(f"❌ 3-Agent pipeline failed: {str(e)}", exc_info=True)
        
        # Return error response in same format
        return {
            "workflow_id": workflow_id,
            "session_id": session_id,
            "status": "error", 
            "immediate_response": f"❌ Pipeline Error: {str(e)}",
            "final_output": {
                "error": str(e),
                "error_type": type(e).__name__,
                "original_request": message,
                "failed_at": "LangChain execution",
                "execution_history": execution_history
            },
            "execution_history": execution_history,
            "total_execution_time_ms": (time.time() - start_time) * 1000,
            "timestamp": datetime.utcnow().isoformat()
        }
