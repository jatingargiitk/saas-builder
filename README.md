# SaaS-Builder: The AI-Native SaaS Framework

Generate production-ready SaaS apps instantly, powered by autonomous AI Agents.

## 🚀 What is SaaS-Builder?

SaaS-Builder is an AI-native framework designed to transform high-level ideas into fully functional SaaS applications rapidly, effortlessly, and at scale.

Powered by cutting-edge AI models, SaaS-Builder automatically scaffolds full-stack React apps with Flask backend and SQLite database, built-in authentication, real-time features, complete TypeScript integration, and production-grade database schemas.

## ✨ Key Features

- 🤖 **AI-Powered Generation**: Instantly build full-stack React apps with Flask & SQLite
- 🏗️ **Complete Application Stack**: Frontend (React), backend (Flask), authentication , data persistence  all handled automatically
- 🔐 **Integrated Authentication**: Seamless Flask auth setup with protected routes
- 🎯 **TypeScript First**: Clean, strongly-typed React codebases by default
- ⚡ **Real-time Capabilities**: Real-time features via Flask integration
- 📊 **Automated Database Setup**: Auto-generated SQLite schemas and migrations

## 🎥 Project Demo

Watch our project demo to see SaaS-Builder in action:

[▶️ Watch Demo Video](https://gocodeo-asset.s3.ap-south-1.amazonaws.com/saas-builder.mp4)

See how easily you can:
- Generate a complete SaaS application from scratch
- Set up authentication and database
- Deploy your application
- And much more!

## 📦 Quick Start

### Installation

Install from PyPI:

```bash
pip install saas-builder
```

Or install from source:

```bash
git clone https://github.com/jatingargiitk/saas-builder.git
cd saas-builder
pip install -e .
```

## 🛠️ Usage

Start a new SaaS project effortlessly:

```bash
saas-builder init
```

### Interactive Setup Flow

Running `saas-builder init` guides you through:

✅ **Project Name & Description**

📋 **Template Selection**
- E-commerce Template
- SaaS Marketing Template
- CRM Template
- Default Template

🧩 **Tech Stack Selection**
- React (UI Only): For frontend-only projects
- React + Flask + SQLite: For full-stack projects with authentication, data persistence, and real-time features

🔑 **Database Configuration**
- SQLite database auto-setup

🤖 **AI Model Selection**
- Claude 3.7 Sonnet (Anthropic)
- GPT-4.1 (OpenAI)
- Gemini 2.5 Pro (Google)

## 🔑 API Keys Setup

Create a `.env` file with your API key(s):

```env
# Claude
ANTHROPIC_API_KEY=your_anthropic_api_key

# GPT-4.1
OPENAI_API_KEY=your_openai_api_key

# Gemini
GOOGLE_API_KEY=your_google_api_key
```

Only one API key (for your chosen model) is required.



## 🏗️ Behind-the-Scenes Build Steps

The SaaS-Builder CLI handles:

| Task | Details |
|------|---------|
| Project Initialization | Scaffold React + Flask project with TypeScript integration |
| Authentication Setup | Integrated Flask Auth with UI & route protection |
| Database Schema | Automatic SQLite DB setup, models, and migrations |
| Dependency Installation | npm & pip dependencies and dev environment configuration |
| Real-time Setup | Native integration of Flask real-time capabilities |
| Development Server | Auto-start React and Flask dev servers for immediate preview |

## 📝 Example Output

```
✅ Build complete!
╭─────────────── Build Summary ───────────────╮
│                                             │
│ Project:       task-manager                 │
│ Description:   App for managing tasks       │
│ Tech Stack:    React + Flask + SQLite      │
│ Files Created: 42                           │
│ Status:        FINISHED                     │
│                                             │
╰─────────────────────────────────────────────╯
```

## 🌟 Our Vision

SaaS-Builder aims to revolutionize application development, leveraging advanced AI to automate the creation of full-stack SaaS products, empowering developers to focus purely on innovation and unique business logic.

## 🎯 Our Mission

To build the most intuitive, powerful AI-native SaaS generation framework making software development dramatically faster, simpler, and more creative.

## 🤝 Contributing

Join our open-source community and help shape the future:

- 🌱 Fork and improve the repo
- 🛠️ Submit pull requests with features or fixes
- 💡 Share your suggestions and feedback on GitHub issues

## 📄 License

Licensed under MIT – see LICENSE for details.

## 🔗 Useful Links

- GitHub: [github.com/jatingargiitk/saas-builder](https://github.com/jatingargiitk/saas-builder)
- PyPI: [pypi.org/project/saas-builder](https://pypi.org/project/saas-builder)
- Documentation: Coming soon!

⭐ Support the framework by starring the repo!

**SaaS-Builder   SaaS app development reimagined.**
