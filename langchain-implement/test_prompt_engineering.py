"""
Test the Prompt Engineering Workflow
"""

import asyncio
import requests
import json
from datetime import datetime

# Test data for prompt engineering
test_cases = [
    {
        "name": "Code Review Agent",
        "message": "Create a system prompt for an AI agent that analyzes GitHub pull requests for code quality, security vulnerabilities, and adherence to best practices. The agent should provide structured feedback with specific recommendations and a quality score.",
        "expected_sections": ["ROLE", "OBJECTIVE", "CONTEXT", "TASK BREAKDOWN", "CONSTRAINTS", "SAFETY & COMPLIANCE", "OUTPUT FORMAT", "STRICT JSON SCHEMA"]
    },
    {
        "name": "Voice Agent System",
        "message": "Design a system prompt for a voice AI agent that handles customer service calls for an e-commerce platform. The agent needs to understand intent, access customer data, handle refunds, and escalate complex issues.",
        "expected_sections": ["ROLE", "OBJECTIVE", "DOMAIN KNOWLEDGE", "CONSTRAINTS", "COMPLETION CRITERIA"]
    },
    {
        "name": "Data Analysis Agent",
        "message": "Create a system prompt for an AI agent that performs statistical analysis on large datasets, identifies patterns, and generates business intelligence reports for executive leadership.",
        "expected_sections": ["ROLE", "OBJECTIVE", "TASK BREAKDOWN", "OUTPUT FORMAT", "ENGINEERING NOTES"]
    }
]

def test_local_workflow():
    """Test the workflow locally using the n8n_workflow_engine directly"""
    
    print("🧪 Testing Prompt Engineering Workflow Locally")
    print("="*60)
    
    async def run_local_test():
        from n8n_workflow_engine import WorkflowEngine, create_prompt_engineering_workflow
        
        engine = WorkflowEngine()
        workflow = create_prompt_engineering_workflow()
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: {test_case['name']}")
            print("-" * 40)
            
            try:
                result = await engine.execute_workflow(
                    workflow,
                    {
                        'message': test_case['message'],
                        'metadata': {'test_case': test_case['name']}
                    },
                    session_id=f'test_session_{i}'
                )
                
                print(f"✅ Status: {result['status']}")
                print(f"⏱️  Execution time: {result['total_execution_time_ms']:.2f}ms")
                
                # Check execution history
                print("\n📊 Agent Execution:")
                for step in result['execution_history']:
                    status_icon = "✅" if step['status'] == 'completed' else "❌"
                    print(f"   {status_icon} {step['node_id']} ({step['execution_time_ms']:.2f}ms)")
                    if step.get('error'):
                        print(f"      Error: {step['error']}")
                
                # Preview final output
                final_output = result.get('final_output', {})
                if isinstance(final_output, dict) and 'final_prompt_template' in final_output:
                    template = final_output['final_prompt_template']
                    print(f"\n📝 Template Preview: {template[:200]}...")
                    
                    # Check for expected sections
                    found_sections = []
                    for section in test_case['expected_sections']:
                        if f"# {section}" in template or f"#{section}" in template:
                            found_sections.append(section)
                    
                    print(f"📋 Found sections: {len(found_sections)}/{len(test_case['expected_sections'])}")
                    print(f"   Found: {found_sections}")
                    missing = set(test_case['expected_sections']) - set(found_sections)
                    if missing:
                        print(f"   Missing: {list(missing)}")
                else:
                    print(f"\n📝 Raw Output: {final_output}")
                
            except Exception as e:
                print(f"❌ Test failed: {str(e)}")
            
            print("-" * 40)
    
    asyncio.run(run_local_test())

def test_api_endpoint():
    """Test the FastAPI endpoint if running"""
    
    print("\n🌐 Testing FastAPI Endpoint")
    print("="*60)
    
    base_url = "http://localhost:8000"
    
    # Test health check first
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Server is running")
            print(f"📊 Health check: {health_response.json()}")
        else:
            print("❌ Server health check failed")
            return
    except requests.exceptions.RequestException:
        print("❌ Server not accessible at localhost:8000")
        print("💡 To test API endpoint, run: python main_enhanced.py")
        return
    
    # Test prompt engineering endpoint
    for i, test_case in enumerate(test_cases[:1], 1):  # Test just the first case for API
        print(f"\n{i}. Testing API: {test_case['name']}")
        
        payload = {
            "message": test_case['message'],
            "session_id": f"api_test_{i}",
            "metadata": {"test_case": test_case['name'], "api_test": True}
        }
        
        try:
            print("📤 Sending request...")
            response = requests.post(
                f"{base_url}/prompt-engineering",
                json=payload,
                timeout=120  # 2 minutes for complex workflow
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Request successful")
                print(f"⏱️  Execution time: {result['total_execution_time_ms']:.2f}ms")
                print(f"📋 Status: {result['status']}")
                print(f"📝 Final output preview: {str(result['final_output'])[:200]}...")
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"Error: {response.text}")
        
        except requests.exceptions.Timeout:
            print("⏱️  Request timed out (this may be normal for complex workflows)")
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {str(e)}")

def main():
    """Run all tests"""
    print("🚀 Prompt Engineering Workflow Test Suite")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Test cases: {len(test_cases)}")
    
    # Test 1: Local workflow engine
    test_local_workflow()
    
    # Test 2: FastAPI endpoint (if available)
    test_api_endpoint()
    
    print("\n🎯 Test Suite Complete!")
    print("="*80)

if __name__ == "__main__":
    main()