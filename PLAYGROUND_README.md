# 🎮 Multi-Model Prompt Playground

## Overview
The Multi-Model Prompt Playground allows you to compare and contrast outputs from multiple LLMs (Gemini, Azure OpenAI GPT-4, GPT-3.5) under the same system instruction and user prompt. This helps teams benchmark prompt effectiveness, identify model strengths, and assess reasoning quality.

## Features

### ✨ Core Functionality
- **Unified Prompt Interface**: Single editor for system instructions and user prompts
- **Multi-Model Comparison**: Run the same prompt across multiple models simultaneously
- **Side-by-Side Results**: Compare model outputs in a split-view layout
- **Performance Metrics**: View latency, token usage, and cost estimates for each model
- **AI Meta-Analysis**: Gemini 2.5 analyzes all outputs and provides structured scoring

### 📊 Metrics Dashboard
Each model result displays:
- **Response**: The full model output
- **Latency**: Time taken to generate the response
- **Tokens**: Total tokens used
- **Cost**: Estimated API cost
- **Status**: Success, Error, or Configuration Required

### 🧠 Meta-Analysis Scores
Gemini 2.5 provides MAANG-level analysis:
- **Clarity Score** (0-10): How clear and understandable the response is
- **Relevance Score** (0-10): How relevant the response is to the prompt
- **Factual Accuracy** (0-10): Correctness of information provided
- **Reasoning Quality** (0-10): Quality of logical reasoning
- **Conciseness** (0-10): Efficiency of communication
- **Overall Summary**: Detailed comparison and recommendations

## Setup

### 1. Environment Variables
Add these to your `.env` file:

```bash
# Gemini API (Required)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent

# Azure OpenAI (Required for GPT models)
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_OPENAI_API_KEY=your-azure-openai-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_GPT4=gpt-4
AZURE_OPENAI_DEPLOYMENT_GPT35=gpt-35-turbo

# Anthropic (Optional - for Claude)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
```

### 2. Access the Playground
1. Navigate to `http://localhost:5001/playground` in your browser
2. Or click the "Prompt Playground" button (compare arrows icon) in the sidebar of the home page

## Usage

### Basic Workflow

1. **Enter System Instruction** (Optional)
   - Provide context that applies to all models
   - Example: "You are a helpful AI assistant specializing in Python programming."

2. **Enter User Prompt** (Required)
   - The actual question or task you want to test
   - Example: "Explain recursion in Python with a simple example."

3. **Select Models**
   - Click on model cards to select/deselect
   - At least one model must be selected
   - Available models:
     - ✅ Gemini 2.0 Flash (Enabled by default)
     - ✅ GPT-4 Turbo (Azure OpenAI)
     - ✅ GPT-3.5 Turbo (Azure OpenAI)
     - ⏳ Claude 3 Opus (Coming soon)

4. **Click Analyze**
   - All selected models will process your prompt simultaneously
   - Results appear in individual cards with metrics
   - Gemini meta-analysis appears below with scores

### Example Prompts to Try

**Code Generation:**
```
System: You are an expert Python developer.
Prompt: Write a function to find the longest palindrome substring in a string.
```

**Creative Writing:**
```
System: You are a creative storyteller.
Prompt: Write the opening paragraph of a sci-fi novel about AI consciousness.
```

**Data Analysis:**
```
System: You are a data scientist.
Prompt: Explain the difference between random forest and gradient boosting algorithms.
```

## API Endpoints

### POST `/api/playground/run_prompt`
Run a prompt across multiple models.

**Request:**
```json
{
  "system_instruction": "You are a helpful assistant",
  "prompt": "What is machine learning?",
  "models": ["gemini-2.0-flash-exp", "gpt-4-turbo", "gpt-3.5-turbo"]
}
```

**Response:**
```json
{
  "results": [
    {
      "model": "gemini-2.0-flash-exp",
      "response": "Machine learning is...",
      "status": "Success",
      "metadata": {
        "latency": 2.13,
        "tokens": 368,
        "cost_estimate": 0.0013
      }
    }
  ],
  "total_time": 4.5
}
```

### POST `/api/playground/analyze_results`
Get meta-analysis from Gemini.

**Request:**
```json
{
  "results": [...],
  "original_prompt": "What is machine learning?"
}
```

**Response:**
```json
{
  "analysis": {
    "clarity_score": 8.9,
    "relevance_score": 9.4,
    "factual_accuracy": 8.6,
    "reasoning_quality": 9.1,
    "conciseness": 8.2,
    "overall_summary": "Gemini 2.5 Pro and GPT-4 Turbo performed comparably..."
  }
}
```

## Troubleshooting

### "Configuration Required" Error
- **Gemini**: Ensure `GEMINI_API_KEY` is set in your `.env` file
- **Azure OpenAI**: Ensure `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_API_KEY` are set
- **Claude**: Add `ANTHROPIC_API_KEY` to enable Claude support

### "API Error" Messages
- Check your API keys are valid and not expired
- Verify you have sufficient credits/quota
- Check your internet connection
- Review the browser console for detailed error messages

### Slow Response Times
- First request to a model may be slower (cold start)
- Running multiple models in parallel takes longer
- Consider selecting fewer models for faster results

### Cost Management
- Monitor the cost estimates shown for each request
- Use GPT-3.5 Turbo for cost-effective testing
- Gemini 2.0 Flash is generally the most economical option

## Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (HTML/JS)                    │
│  ┌────────────┐  ┌────────────┐  ┌────────────────┐    │
│  │  System    │  │   User     │  │     Model      │    │
│  │Instruction │  │   Prompt   │  │   Selection    │    │
│  └────────────┘  └────────────┘  └────────────────┘    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Flask Backend (app.py)                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │     /api/playground/run_prompt                   │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │   │
│  │  │  Gemini  │  │Azure GPT4│  │Azure GPT │      │   │
│  │  │   API    │  │   API    │  │ 3.5 API  │      │   │
│  │  └──────────┘  └──────────┘  └──────────┘      │   │
│  └─────────────────────────────────────────────────┘   │
│                          │                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │    /api/playground/analyze_results               │   │
│  │             (Gemini Meta-Analysis)               │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    Results Display                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Model 1  │  │ Model 2  │  │ Model 3  │              │
│  │ Response │  │ Response │  │ Response │              │
│  │ Metrics  │  │ Metrics  │  │ Metrics  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│  ┌──────────────────────────────────────────┐          │
│  │         Meta-Analysis Scores              │          │
│  │  Clarity | Relevance | Accuracy | ...     │          │
│  │         Overall Summary                    │          │
│  └──────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────┘
```

## Roadmap

### Phase 1: MVP (Current)
- ✅ Multi-model prompt comparison
- ✅ Gemini meta-analysis
- ✅ Basic metrics (latency, tokens, cost)
- ✅ Azure OpenAI integration

### Phase 2: Enhanced Features
- [ ] Prompt versioning and history
- [ ] CSV/JSON export of results
- [ ] Advanced metrics (semantic similarity, diversity)
- [ ] Custom model selection
- [ ] Batch testing

### Phase 3: Advanced Analytics
- [ ] Radar charts for score visualization
- [ ] A/B testing framework
- [ ] Prompt optimization suggestions
- [ ] Team collaboration features
- [ ] Supabase integration for persistent storage

## Contributing

To extend the playground with additional models:

1. Add the model configuration to `app.py`
2. Implement a `call_<model>_model()` function
3. Add the model to the frontend selection in `playground.html`
4. Update the model mapping in `playground.js`

## Support

For issues or questions:
- Check the browser console for error messages
- Review the Flask logs in `logs/detections.log`
- Ensure all API keys are correctly configured
- Verify you're using the latest version of the code

---

**Built with ❤️ for MAANG-level prompt engineering**
