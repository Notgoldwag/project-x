"""
N8N-Style Workflow Engine for LangChain Multi-Agent Systems
Dynamic workflow configuration and execution engine
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel
import logging
from datetime import datetime
import uuid

from langchain_openai import AzureChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

logger = logging.getLogger(__name__)

class NodeType(str, Enum):
    """Available node types in the workflow"""
    WEBHOOK = "webhook"
    CODE = "code"  
    AI_AGENT = "ai_agent"
    WORKFLOW_CONFIG = "workflow_config"
    OUTPUT_PASS = "output_pass"
    HTTP_REQUEST = "http_request"
    CONDITIONAL = "conditional"
    MEMORY = "memory"

class NodeStatus(str, Enum):
    """Node execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class Connection:
    """Represents a connection between workflow nodes"""
    source_node: str
    target_node: str
    condition: Optional[str] = None  # For conditional routing
    output_key: Optional[str] = None  # Which output to pass

@dataclass
class NodeConfig:
    """Configuration for a workflow node"""
    node_id: str
    node_type: NodeType
    name: str
    config: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, int] = field(default_factory=dict)  # For UI positioning

@dataclass
class WorkflowDefinition:
    """Complete workflow definition matching n8n structure"""
    workflow_id: str
    name: str
    nodes: List[NodeConfig]
    connections: List[Connection]
    settings: Dict[str, Any] = field(default_factory=dict)

class NodeExecutionResult:
    """Result of executing a single node"""
    def __init__(
        self, 
        node_id: str, 
        status: NodeStatus, 
        output: Any = None, 
        error: str = None,
        execution_time_ms: float = 0
    ):
        self.node_id = node_id
        self.status = status
        self.output = output
        self.error = error
        self.execution_time_ms = execution_time_ms
        self.timestamp = datetime.utcnow()

class WorkflowContext:
    """Context maintained throughout workflow execution"""
    def __init__(self, workflow_id: str, session_id: str = None):
        self.workflow_id = workflow_id
        self.session_id = session_id or str(uuid.uuid4())
        self.data: Dict[str, Any] = {}
        self.node_outputs: Dict[str, Any] = {}
        self.execution_history: List[NodeExecutionResult] = []
        self.memory_store = ChatMessageHistory()
    
    def set_node_output(self, node_id: str, output: Any):
        """Store output from a node"""
        self.node_outputs[node_id] = output
    
    def get_node_output(self, node_id: str) -> Any:
        """Get output from a previous node"""
        return self.node_outputs.get(node_id)
    
    def add_execution_result(self, result: NodeExecutionResult):
        """Add execution result to history"""
        self.execution_history.append(result)

class BaseNode:
    """Base class for all workflow nodes"""
    
    def __init__(self, config: NodeConfig):
        self.config = config
        self.node_id = config.node_id
        self.node_type = config.node_type
        self.name = config.name
    
    async def execute(self, context: WorkflowContext, input_data: Any = None) -> NodeExecutionResult:
        """Execute the node - to be implemented by subclasses"""
        raise NotImplementedError
    
    def validate_config(self) -> bool:
        """Validate node configuration"""
        return True

class WebhookNode(BaseNode):
    """Webhook trigger node"""
    
    async def execute(self, context: WorkflowContext, input_data: Any = None) -> NodeExecutionResult:
        start_time = datetime.utcnow()
        
        try:
            # Process webhook input
            webhook_data = input_data or {}
            
            # Store in context
            context.data['webhook_input'] = webhook_data
            
            # Immediate response configuration
            immediate_response = self.config.config.get('immediate_response', 'Request received')
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return NodeExecutionResult(
                node_id=self.node_id,
                status=NodeStatus.COMPLETED,
                output={
                    'immediate_response': immediate_response,
                    'webhook_data': webhook_data
                },
                execution_time_ms=execution_time
            )
        
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return NodeExecutionResult(
                node_id=self.node_id,
                status=NodeStatus.FAILED,
                error=str(e),
                execution_time_ms=execution_time
            )

class CodeNode(BaseNode):
    """JavaScript/Python code execution node"""
    
    async def execute(self, context: WorkflowContext, input_data: Any = None) -> NodeExecutionResult:
        start_time = datetime.utcnow()
        
        try:
            # Get code from configuration
            code = self.config.config.get('code', '')
            language = self.config.config.get('language', 'javascript')
            
            if language == 'javascript':
                # Simulate JavaScript execution
                # In production, you'd use a proper JS engine like PyMiniRacer
                result = self._simulate_js_execution(code, input_data, context)
            else:
                # Execute Python code (be careful with security!)
                result = self._execute_python_code(code, input_data, context)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return NodeExecutionResult(
                node_id=self.node_id,
                status=NodeStatus.COMPLETED,
                output=result,
                execution_time_ms=execution_time
            )
        
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return NodeExecutionResult(
                node_id=self.node_id,
                status=NodeStatus.FAILED,
                error=str(e),
                execution_time_ms=execution_time
            )
    
    def _simulate_js_execution(self, code: str, input_data: Any, context: WorkflowContext) -> Dict[str, Any]:
        """Simulate JavaScript execution"""
        # This is a simple simulation - in production use PyMiniRacer or similar
        return {
            'processed': True,
            'input_data': input_data,
            'code_executed': code[:100] + "..." if len(code) > 100 else code
        }
    
    def _execute_python_code(self, code: str, input_data: Any, context: WorkflowContext) -> Dict[str, Any]:
        """Execute Python code safely (restricted environment)"""
        # WARNING: This is unsafe for production without proper sandboxing
        safe_globals = {
            'input_data': input_data,
            'context_data': context.data,
            'json': json,
            'datetime': datetime
        }
        
        local_vars = {}
        exec(code, safe_globals, local_vars)
        
        return local_vars.get('result', local_vars)

class AIAgentNode(BaseNode):
    """AI Agent execution node with Azure OpenAI"""
    
    def __init__(self, config: NodeConfig, llm_factory=None):
        super().__init__(config)
        self.llm_factory = llm_factory
    
    async def execute(self, context: WorkflowContext, input_data: Any = None) -> NodeExecutionResult:
        start_time = datetime.utcnow()
        
        try:
            # Get agent configuration
            agent_config = self.config.config
            model_config = agent_config.get('model', {})
            prompt_template = agent_config.get('prompt', '')
            memory_enabled = agent_config.get('memory', True)
            
            # Create LLM
            llm = self._create_llm(model_config)
            
            # Create agent
            agent = self._create_agent(llm, prompt_template, memory_enabled, context)
            
            # Prepare input
            agent_input = self._prepare_agent_input(input_data, context)
            
            # Execute agent
            response = await agent.ainvoke(
                {"input": agent_input},
                config={"configurable": {"session_id": context.session_id}} if memory_enabled else {}
            )
            
            output = response.get("output", "")
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return NodeExecutionResult(
                node_id=self.node_id,
                status=NodeStatus.COMPLETED,
                output={
                    'agent_response': output,
                    'model_used': model_config.get('deployment', 'gpt-4'),
                    'memory_enabled': memory_enabled
                },
                execution_time_ms=execution_time
            )
        
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return NodeExecutionResult(
                node_id=self.node_id,
                status=NodeStatus.FAILED,
                error=str(e),
                execution_time_ms=execution_time
            )
    
    def _create_llm(self, model_config: Dict[str, Any]) -> AzureChatOpenAI:
        """Create Azure OpenAI LLM instance"""
        if self.llm_factory:
            return self.llm_factory(model_config)
        
        # Default LLM creation
        return AzureChatOpenAI(
            azure_deployment=model_config.get('deployment', 'gpt-4'),
            temperature=model_config.get('temperature', 0.7),
            max_tokens=model_config.get('max_tokens', 1000),
            timeout=30,
            max_retries=3
        )
    
    def _create_agent(
        self, 
        llm: AzureChatOpenAI, 
        prompt_template: str, 
        memory_enabled: bool,
        context: WorkflowContext
    ) -> Union[AgentExecutor, RunnableWithMessageHistory]:
        """Create configured agent"""
        
        # Create tools based on configuration
        tools = self._create_tools()
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_template or "You are a helpful AI assistant."),
            MessagesPlaceholder(variable_name="chat_history") if memory_enabled else ("human", ""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create agent
        agent = create_openai_tools_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )
        
        if memory_enabled:
            # Wrap with memory
            return RunnableWithMessageHistory(
                agent_executor,
                lambda session_id: context.memory_store,
                input_messages_key="input",
                history_messages_key="chat_history"
            )
        
        return agent_executor
    
    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent"""
        tools = []
        tool_configs = self.config.config.get('tools', [])
        
        for tool_config in tool_configs:
            tool = Tool(
                name=tool_config.get('name', 'generic_tool'),
                func=lambda x: f"Tool executed: {x}",  # Placeholder
                description=tool_config.get('description', 'Generic tool')
            )
            tools.append(tool)
        
        return tools
    
    def _prepare_agent_input(self, input_data: Any, context: WorkflowContext) -> str:
        """Prepare input for the agent"""
        if isinstance(input_data, dict):
            if 'message' in input_data:
                return input_data['message']
            elif 'input' in input_data:
                return input_data['input']
            else:
                return json.dumps(input_data)
        elif isinstance(input_data, str):
            return input_data
        else:
            return str(input_data)

class OutputPassNode(BaseNode):
    """Node that passes output from one agent to another"""
    
    async def execute(self, context: WorkflowContext, input_data: Any = None) -> NodeExecutionResult:
        start_time = datetime.utcnow()
        
        try:
            # Get configuration
            source_node = self.config.config.get('source_node')
            output_mapping = self.config.config.get('output_mapping', {})
            
            # Get source data
            if source_node:
                source_output = context.get_node_output(source_node)
            else:
                source_output = input_data
            
            # Apply transformations
            transformed_output = self._transform_output(source_output, output_mapping)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return NodeExecutionResult(
                node_id=self.node_id,
                status=NodeStatus.COMPLETED,
                output=transformed_output,
                execution_time_ms=execution_time
            )
        
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return NodeExecutionResult(
                node_id=self.node_id,
                status=NodeStatus.FAILED,
                error=str(e),
                execution_time_ms=execution_time
            )
    
    def _transform_output(self, output: Any, mapping: Dict[str, str]) -> Dict[str, Any]:
        """Transform output according to mapping rules"""
        if not mapping:
            return output
        
        transformed = {}
        for target_key, source_path in mapping.items():
            # Simple path resolution (e.g., "response.content")
            value = self._resolve_path(output, source_path)
            transformed[target_key] = value
        
        return transformed
    
    def _resolve_path(self, data: Any, path: str) -> Any:
        """Resolve a dot-notation path in data"""
        parts = path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                return None
        
        return current

class WorkflowEngine:
    """Main workflow execution engine"""
    
    def __init__(self, llm_factory=None):
        self.llm_factory = llm_factory
        self.node_factories = {
            NodeType.WEBHOOK: WebhookNode,
            NodeType.CODE: CodeNode,
            NodeType.AI_AGENT: lambda config: AIAgentNode(config, self.llm_factory),
            NodeType.OUTPUT_PASS: OutputPassNode,
        }
    
    async def execute_workflow(
        self, 
        workflow_def: WorkflowDefinition, 
        initial_data: Any = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """Execute a complete workflow"""
        
        context = WorkflowContext(workflow_def.workflow_id, session_id)
        context.data['initial_input'] = initial_data
        
        logger.info(f"Starting workflow execution: {workflow_def.name}")
        
        # Find entry point (webhook node)
        entry_nodes = [node for node in workflow_def.nodes if node.node_type == NodeType.WEBHOOK]
        if not entry_nodes:
            raise ValueError("Workflow must have a webhook entry point")
        
        # Execute nodes in order
        executed_nodes = set()
        execution_queue = [entry_nodes[0].node_id]
        
        while execution_queue:
            current_node_id = execution_queue.pop(0)
            
            if current_node_id in executed_nodes:
                continue
            
            # Find node definition
            node_config = next(
                (node for node in workflow_def.nodes if node.node_id == current_node_id), 
                None
            )
            
            if not node_config:
                logger.error(f"Node {current_node_id} not found in workflow")
                continue
            
            # Create and execute node
            node = self._create_node(node_config)
            input_data = self._get_node_input(current_node_id, context, workflow_def)
            
            logger.info(f"Executing node: {current_node_id} ({node_config.node_type})")
            
            result = await node.execute(context, input_data)
            context.add_execution_result(result)
            
            if result.status == NodeStatus.COMPLETED:
                context.set_node_output(current_node_id, result.output)
                executed_nodes.add(current_node_id)
                
                # Add connected nodes to queue
                next_nodes = self._get_next_nodes(current_node_id, workflow_def)
                execution_queue.extend(next_nodes)
            else:
                logger.error(f"Node {current_node_id} failed: {result.error}")
                # Handle failure according to workflow settings
        
        # Prepare final response
        return self._prepare_workflow_response(context, workflow_def)
    
    def _create_node(self, config: NodeConfig) -> BaseNode:
        """Create a node instance from configuration"""
        node_factory = self.node_factories.get(config.node_type)
        if not node_factory:
            raise ValueError(f"Unknown node type: {config.node_type}")
        
        return node_factory(config)
    
    def _get_node_input(
        self, 
        node_id: str, 
        context: WorkflowContext, 
        workflow_def: WorkflowDefinition
    ) -> Any:
        """Get input data for a node"""
        
        # Find incoming connections
        incoming = [conn for conn in workflow_def.connections if conn.target_node == node_id]
        
        if not incoming:
            # Entry node - use initial data
            return context.data.get('initial_input')
        
        # Collect inputs from source nodes
        inputs = {}
        for connection in incoming:
            source_output = context.get_node_output(connection.source_node)
            if connection.output_key:
                source_output = source_output.get(connection.output_key) if isinstance(source_output, dict) else source_output
            inputs[connection.source_node] = source_output
        
        # If single input, return directly; if multiple, return dict
        if len(inputs) == 1:
            return list(inputs.values())[0]
        return inputs
    
    def _get_next_nodes(self, node_id: str, workflow_def: WorkflowDefinition) -> List[str]:
        """Get next nodes to execute"""
        outgoing = [conn for conn in workflow_def.connections if conn.source_node == node_id]
        return [conn.target_node for conn in outgoing]
    
    def _prepare_workflow_response(
        self, 
        context: WorkflowContext, 
        workflow_def: WorkflowDefinition
    ) -> Dict[str, Any]:
        """Prepare final workflow response"""
        
        # Find final output
        final_output = None
        if context.node_outputs:
            # Get output from last executed node
            last_result = context.execution_history[-1] if context.execution_history else None
            if last_result and last_result.status == NodeStatus.COMPLETED:
                final_output = context.get_node_output(last_result.node_id)
        
        # Calculate total execution time
        total_time = sum(result.execution_time_ms for result in context.execution_history)
        
        return {
            'workflow_id': context.workflow_id,
            'session_id': context.session_id,
            'status': 'completed',
            'final_output': final_output,
            'execution_history': [
                {
                    'node_id': result.node_id,
                    'status': result.status.value,
                    'execution_time_ms': result.execution_time_ms,
                    'error': result.error
                }
                for result in context.execution_history
            ],
            'total_execution_time_ms': total_time,
            'timestamp': datetime.utcnow().isoformat()
        }

# MAANG-Grade Prompt Engineering Workflow
def create_prompt_engineering_workflow() -> WorkflowDefinition:
    """Create a workflow for MAANG-grade prompt engineering with 3 specialized agents"""
    
    return WorkflowDefinition(
        workflow_id=str(uuid.uuid4()),
        name="MAANG-Grade Prompt Engineering Workflow",
        nodes=[
            NodeConfig(
                node_id="webhook_1",
                node_type=NodeType.WEBHOOK,
                name="Webhook",
                config={
                    'immediate_response': 'Processing your prompt engineering request through our 3-agent pipeline...',
                    'method': 'POST'
                }
            ),
            NodeConfig(
                node_id="code_1", 
                node_type=NodeType.CODE,
                name="Code in JavaScript",
                config={
                    'language': 'javascript',
                    'code': '''
                    // Preprocess input for prompt engineering workflow
                    const result = {
                        processed: true,
                        task_description: input_data.message,
                        timestamp: new Date().toISOString(),
                        workflow_stage: "preprocessing",
                        user_requirements: input_data.metadata || {}
                    };
                    return result;
                    '''
                }
            ),
            NodeConfig(
                node_id="workflow_config_1",
                node_type=NodeType.OUTPUT_PASS,
                name="Workflow Configuration",
                config={
                    'manual': True,
                    'output_mapping': {
                        'task_input': 'task_description',
                        'workflow_context': 'processed_data'
                    }
                }
            ),
            NodeConfig(
                node_id="agent_1_prompt_architect",
                node_type=NodeType.AI_AGENT,
                name="Agent 1 - Prompt Architect",
                config={
                    'model': {
                        'deployment': 'gpt-4',
                        'temperature': 0.3,  # Lower for more deterministic prompt generation
                        'max_tokens': 2000
                    },
                    'prompt': '''You are Agent 1 — a Prompt Architect responsible for generating developer-friendly, MAANG-grade system instruction templates.

Your ONLY job is to produce a clear, readable, multi-section system prompt that a downstream AI agent will use to perform the task. You must NOT perform the task. You must NOT output results or JSON for the task itself. You must NOT analyze code, PRs, data, or user content.

OUTPUT GOAL:
Produce a developer-friendly prompt template that contains the following exact sections:

# ROLE  
# OBJECTIVE  
# CONTEXT  
# TASK BREAKDOWN  
# DOMAIN KNOWLEDGE (if needed)  
# CONSTRAINTS  
# SAFETY & COMPLIANCE  
# OUTPUT FORMAT  
# STRICT JSON SCHEMA  
# COMPLETION CRITERIA  
# ENGINEERING NOTES  

REQUIREMENTS:
• The template must be written for developers, not for runtime execution.
• DO NOT minify. Use spacing, headings, and indentation.
• DO NOT perform the task you are describing.
• DO NOT output placeholders like <insert_here>. Write complete sections.
• Infer relevant industry best practices (MAANG level).
• If domain knowledge is needed, retrieve it conceptually but describe it only inside the template.
• Do not produce code unless it is part of the schema.

FINAL ACTION:
Return ONLY the human-readable system prompt template.''',
                    'memory': True,
                    'tools': []
                }
            ),
            NodeConfig(
                node_id="pass_agent1_output",
                node_type=NodeType.OUTPUT_PASS,
                name="Pass Agent 1 Output",
                config={
                    'source_node': 'agent_1_prompt_architect',
                    'output_mapping': {
                        'prompt_template_v1': 'agent_response'
                    }
                }
            ),
            NodeConfig(
                node_id="agent_2_guardrail_engineer",
                node_type=NodeType.AI_AGENT,
                name="Agent 2 - Guardrail Engineer", 
                config={
                    'model': {
                        'deployment': 'gpt-4',
                        'temperature': 0.2,  # Even lower for careful refinement
                        'max_tokens': 2200
                    },
                    'prompt': '''You are Agent 2 — a Guardrail Engineer. Your task is to refine and audit the system prompt template generated by Agent 1.

You must NOT execute or perform the task described in the template. You must NOT generate task outputs, PR reviews, JSON results, or state objects.

Your responsibilities:
1. Check for missing sections.
2. Ensure section order and formatting is consistent.
3. Strengthen constraints, safety rules, and compliance notes.
4. Remove ambiguity, hallucination risks, and unclear language.
5. Improve structural clarity and developer readability.
6. Ensure all JSON schema sections are precise and MAANG-grade.
7. Prevent the model from drifting into execution mode.
8. Follow MAANG prompt-engineering standards (clarity, determinism, modularity).

Rules:
• Do NOT add runtime examples that resemble task execution.
• Do NOT compress or minify the template.
• Preserve the template style (headings, spacing, indentation).
• You may add missing details, but only template-related details.

FINAL ACTION:
Output ONLY the corrected and enhanced system prompt template.''',
                    'memory': True,
                    'tools': []
                }
            ),
            NodeConfig(
                node_id="pass_agent2_output",
                node_type=NodeType.OUTPUT_PASS,
                name="Pass Agent 2 Output",
                config={
                    'source_node': 'agent_2_guardrail_engineer',
                    'output_mapping': {
                        'prompt_template_v2': 'agent_response'
                    }
                }
            ),
            NodeConfig(
                node_id="agent_3_template_polisher",
                node_type=NodeType.AI_AGENT,
                name="Agent 3 - Template Polisher",
                config={
                    'model': {
                        'deployment': 'gpt-4',
                        'temperature': 0.1,  # Lowest for final polishing
                        'max_tokens': 2500
                    },
                    'prompt': '''You are Agent 3 — the Final Template Polisher. Your ONLY task is to perfect the system prompt template refined by Agent 2.

Your responsibilities:
• Ensure the template is polished, consistent, and professional.
• Ensure section headers, spacing, and indentation follow MAANG standards.
• Ensure clarity, precision, and technical correctness.
• Do NOT change the meaning of any section.
• Do NOT add new task behaviors.
• Do NOT add examples that resemble execution outputs.
• Do NOT generate JSON findings, PR analysis, voice agent actions, or any runtime output.
• Do NOT remove required sections.
• Maintain a developer-friendly readable format — NOT a compact runtime prompt.

STRICT RULE:
You MUST output ONLY the final, polished system prompt template.
If ANY part of your output resembles task execution (e.g., analyzing code, filling slots, generating JSON action frames), your output is INVALID.

FINAL ACTION:
Output ONLY the final developer-friendly prompt template, nothing else.''',
                    'memory': True,
                    'tools': []
                }
            ),
            NodeConfig(
                node_id="final_output",
                node_type=NodeType.OUTPUT_PASS,
                name="Final Template Output",
                config={
                    'source_node': 'agent_3_template_polisher',
                    'output_mapping': {
                        'final_prompt_template': 'agent_response',
                        'workflow_completion': 'completed'
                    }
                }
            ),
            NodeConfig(
                node_id="http_request_1",
                node_type=NodeType.HTTP_REQUEST,
                name="HTTP Request",
                config={
                    'method': 'POST',
                    'url': 'https://your-webhook-endpoint.com/prompt-engineering-complete',
                    'headers': {
                        'Content-Type': 'application/json'
                    }
                }
            )
        ],
        connections=[
            Connection("webhook_1", "code_1"),
            Connection("code_1", "workflow_config_1"),
            Connection("workflow_config_1", "agent_1_prompt_architect"),
            Connection("agent_1_prompt_architect", "pass_agent1_output"),
            Connection("pass_agent1_output", "agent_2_guardrail_engineer"),
            Connection("agent_2_guardrail_engineer", "pass_agent2_output"),
            Connection("pass_agent2_output", "agent_3_template_polisher"),
            Connection("agent_3_template_polisher", "final_output"),
            Connection("final_output", "http_request_1")
        ]
    )

# Keep the original workflow as well for backward compatibility
def create_n8n_workflow_example() -> WorkflowDefinition:
    """Create a general workflow that matches your n8n diagram"""
    
    return WorkflowDefinition(
        workflow_id=str(uuid.uuid4()),
        name="General Multi-Agent Workflow",
        nodes=[
            NodeConfig(
                node_id="webhook_1",
                node_type=NodeType.WEBHOOK,
                name="Webhook",
                config={
                    'immediate_response': 'Processing your request...',
                    'method': 'POST'
                }
            ),
            NodeConfig(
                node_id="code_1", 
                node_type=NodeType.CODE,
                name="Code in JavaScript",
                config={
                    'language': 'javascript',
                    'code': '''
                    const result = {
                        processed: true,
                        message: input_data.message,
                        timestamp: new Date().toISOString()
                    };
                    return result;
                    '''
                }
            ),
            NodeConfig(
                node_id="workflow_config_1",
                node_type=NodeType.OUTPUT_PASS,
                name="Workflow Configuration",
                config={
                    'manual': True,
                    'output_mapping': {
                        'input': 'message',
                        'context': 'processed_data'
                    }
                }
            ),
            NodeConfig(
                node_id="ai_agent_1",
                node_type=NodeType.AI_AGENT,
                name="AI Agent",
                config={
                    'model': {
                        'deployment': 'gpt-4',
                        'temperature': 0.7,
                        'max_tokens': 1000
                    },
                    'prompt': '''You are AI Agent 1. Analyze the user input and extract key information. 
                    Provide a structured response with:
                    1. Intent analysis
                    2. Key entities
                    3. Recommended next steps''',
                    'memory': True,
                    'tools': []
                }
            ),
            NodeConfig(
                node_id="pass_agent1_output",
                node_type=NodeType.OUTPUT_PASS,
                name="Pass Agent 1 Output",
                config={
                    'source_node': 'ai_agent_1',
                    'output_mapping': {
                        'agent1_analysis': 'agent_response'
                    }
                }
            ),
            NodeConfig(
                node_id="ai_agent_2",
                node_type=NodeType.AI_AGENT,
                name="AI Agent 2", 
                config={
                    'model': {
                        'deployment': 'gpt-4',
                        'temperature': 0.7,
                        'max_tokens': 1200
                    },
                    'prompt': '''You are AI Agent 2. Based on the analysis from Agent 1, provide:
                    1. Detailed recommendations
                    2. Action plan
                    3. Next steps
                    4. Final comprehensive response
                    
                    Use the context from Agent 1 to build upon their analysis.''',
                    'memory': True,
                    'tools': []
                }
            ),
            NodeConfig(
                node_id="pass_agent2_output",
                node_type=NodeType.OUTPUT_PASS,
                name="Pass Agent 2 Output",
                config={
                    'source_node': 'ai_agent_2',
                    'output_mapping': {
                        'final_response': 'agent_response'
                    }
                }
            ),
            NodeConfig(
                node_id="http_request_1",
                node_type=NodeType.HTTP_REQUEST,
                name="HTTP Request",
                config={
                    'method': 'POST',
                    'url': 'https://your-webhook-endpoint.com/callback',
                    'headers': {
                        'Content-Type': 'application/json'
                    }
                }
            )
        ],
        connections=[
            Connection("webhook_1", "code_1"),
            Connection("code_1", "workflow_config_1"),
            Connection("workflow_config_1", "ai_agent_1"),
            Connection("ai_agent_1", "pass_agent1_output"),
            Connection("pass_agent1_output", "ai_agent_2"),
            Connection("ai_agent_2", "pass_agent2_output"),
            Connection("pass_agent2_output", "http_request_1")
        ]
    )

# Example usage
async def test_prompt_engineering_workflow():
    """Test the prompt engineering workflow with MAANG-grade agents"""
    
    # Create workflow engine
    engine = WorkflowEngine()
    
    # Create prompt engineering workflow
    workflow = create_prompt_engineering_workflow()
    
    # Test input for prompt engineering
    test_input = {
        'message': '''Create a system prompt for an AI agent that will analyze GitHub pull requests for code quality, security issues, and best practices. The agent should provide structured feedback with recommendations and a quality score.''',
        'metadata': {
            'domain': 'code_review',
            'output_format': 'structured_feedback',
            'complexity': 'high'
        }
    }
    
    print("🎯 Testing MAANG-Grade Prompt Engineering Workflow")
    print("="*60)
    print(f"Input: {test_input['message']}")
    print("="*60)
    
    # Execute workflow
    result = await engine.execute_workflow(
        workflow, 
        test_input,
        session_id='prompt_eng_session_123'
    )
    
    print("\n📊 Workflow Execution Result:")
    print("="*60)
    print(f"Status: {result['status']}")
    print(f"Total time: {result['total_execution_time_ms']:.2f}ms")
    print(f"Session ID: {result['session_id']}")
    
    print("\n🔄 Agent Execution History:")
    for i, step in enumerate(result['execution_history'], 1):
        print(f"{i}. {step['node_id']} - {step['status']} ({step['execution_time_ms']:.2f}ms)")
        if step.get('error'):
            print(f"   ❌ Error: {step['error']}")
    
    print(f"\n🎯 Final Prompt Template:")
    print("="*60)
    if result['final_output'] and 'final_prompt_template' in str(result['final_output']):
        final_template = result['final_output'].get('final_prompt_template', '')
        print(final_template[:500] + "..." if len(final_template) > 500 else final_template)
    else:
        print("Final template not available in expected format")
        print(f"Raw output: {result['final_output']}")

async def test_n8n_workflow():
    """Test the general n8n-style workflow"""
    
    # Create workflow engine
    engine = WorkflowEngine()
    
    # Create workflow definition
    workflow = create_n8n_workflow_example()
    
    # Test input
    test_input = {
        'message': 'I need help planning a sustainable business strategy for my tech startup.',
        'user_id': 'test_user_123'
    }
    
    print("\n🔄 Testing General Multi-Agent Workflow")
    print("="*60)
    
    # Execute workflow
    result = await engine.execute_workflow(
        workflow, 
        test_input,
        session_id='test_session_123'
    )
    
    print("Workflow execution result:")
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    print("🚀 N8N-Style Workflow Engine Test Suite")
    print("="*80)
    
    async def run_all_tests():
        """Run all workflow tests"""
        
        # Test 1: Prompt Engineering Workflow (Your specific use case)
        try:
            await test_prompt_engineering_workflow()
        except Exception as e:
            print(f"❌ Prompt engineering workflow failed: {e}")
        
        print("\n" + "="*80)
        
        # Test 2: General Workflow
        try:
            await test_n8n_workflow()
        except Exception as e:
            print(f"❌ General workflow failed: {e}")
        
        print("\n🎯 Test Suite Complete!")
    
    asyncio.run(run_all_tests())