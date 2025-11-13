# 🚀 Project X

## AI-Powered Prompt Engineering Platform

Welcome to Project X - a comprehensive AI platform featuring prompt engineering, prompt playground, and prompt injection detection capabilities.

## 📁 Project Structure

The repository is organized with a clean feature-based structure:

```
project-x/
├── .env                        # Environment variables
├── .gitignore                  # Git ignore rules
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── index.html                  # Landing page
├── login_signup.html          # Authentication page
├── vercel.json                # Vercel deployment config
│
├── static/                    # Global shared assets
│   ├── css/
│   │   ├── global.css         # Shared styles
│   │   └── bg.css             # Background animation
│   ├── js/
│   │   ├── auth.js            # Authentication logic
│   │   └── bundle.js          # Background animation
│   └── images/                # Shared images
│
├── features/                  # Feature modules
│   ├── prompt_engineering/    # Prompt Engineering feature
│   │   ├── index.html
│   │   └── static/
│   │       ├── css/
│   │       │   └── prompt_engineering.css
│   │       └── js/
│   │           └── prompt_engineering.js
│   │
│   ├── prompt_playground/     # Prompt Playground feature
│   │   ├── index.html
│   │   └── static/
│   │       ├── css/
│   │       └── js/
│   │           └── prompt_playground.js
│   │
│   └── prompt_injection/      # Prompt Injection Detection
│       ├── index.html
│       └── static/
│           ├── css/
│           │   └── prompt_injection.css
│           └── js/
│               └── prompt_injection.js
│
├── api/                       # API modules (future)
├── data/                      # Data files
├── logs/                      # Application logs
│
└── unwanted_files/           # Archive of old/test files
    ├── test_files/           # Test scripts and files
    ├── backup_files/         # Backup/duplicate files
    ├── langchain_old/        # Old langchain implementation
    └── docs/                 # Archived documentation
```

## ✨ Features

### 🎯 **Prompt Engineering**
- AI-powered text editing with real-time suggestions
- LangChain orchestration with multiple agents
- Session-based chat interface
- Metrics visualization and analysis
- Supabase integration for history tracking

### 🎮 **Prompt Playground**
- Multi-model prompt testing (Gemini, OpenAI, Claude)
- Side-by-side comparison of model outputs
- Customizable system instructions
- Results analysis and comparison
- Performance metrics

### 🛡️ **Prompt Injection Detection**
- ML-based injection detection using fine-tuned RoBERTa
- Real-time prompt analysis
- Confidence scoring
- Security logging and monitoring

### 🌌 **Immersive UI**
- Glassmorphic design with advanced blur effects
- Animated background with floating particles
- Dark mode optimized interface
- Responsive and mobile-friendly

## 🛠 Technical Stack

### **Backend**
- **Flask**: Python web framework
- **Transformers**: ML models for prompt injection detection
- **LangChain**: AI orchestration and agent workflows
- **PyTorch**: Deep learning framework

### **Frontend**
- **HTML5/CSS3**: Modern semantic markup
- **Tailwind CSS**: Utility-first styling
- **Vanilla JavaScript**: Lightweight and fast
- **Chart.js**: Data visualization

### **APIs**
- Google Gemini AI
- Azure OpenAI
- Anthropic Claude (planned)

## 🚀 Getting Started

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Notgoldwag/project-x.git
   cd project-x
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**
   Create a `.env` file with:
   ```env
   GEMINI_API_KEY=your_gemini_key
   AZURE_OPENAI_ENDPOINT=your_azure_endpoint
   AZURE_OPENAI_API_KEY=your_azure_key
   ```

4. **Run the Application**
   ```bash
   python app.py
   ```

5. **Access the Platform**
   - Landing Page: `http://127.0.0.1:5001/`
   - Prompt Engineering: `http://127.0.0.1:5001/home`
   - Prompt Playground: `http://127.0.0.1:5001/playground`
   - Injection Detection: `http://127.0.0.1:5001/prompt-injection`

## 📋 API Endpoints

### Prompt Engineering
- `POST /api/chat` - Main chat endpoint with LangChain orchestration
- `POST /api/score_prompt` - Score prompt quality
- `POST /api/analyze_prompt` - Analyze prompt structure
- `POST /api/explain` - Get AI explanation

### Prompt Playground
- `POST /api/playground/run_prompt` - Run prompt across multiple models
- `POST /api/playground/analyze_results` - Analyze and compare results

### Prompt Injection Detection
- `POST /api/prompt_injection_detector/score` - Detect injection attempts
- `POST /api/prompt_injection_detector/explain` - Explain detection results

## 🎨 Customization

### Adding New Features
1. Create a new directory under `features/`
2. Add `index.html` and `static/` subdirectories
3. Register routes in `app.py`
4. Update the Jinja2 loader to include the new feature path

### Styling
- Global styles: `static/css/global.css`
- Feature-specific styles: `features/{feature}/static/css/`
- Background animation: `static/css/bg.css`

## 🔒 Security

- Prompt injection detection using ML models
- Input sanitization and validation
- Secure API key management via environment variables
- Logging of security events

## 📱 Browser Support

- Chrome 88+
- Firefox 87+
- Safari 14+
- Edge 88+

## 🤝 Contributing

This is a private project. For questions or suggestions, please contact the repository owner.

## 📄 License

Proprietary - All rights reserved

---

**Project X** - *Next-generation AI prompt engineering platform* ✨