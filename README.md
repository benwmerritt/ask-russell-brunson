# Ask Russell Brunson - RAG MCP Server

Production-ready **Model Context Protocol (MCP)** server that exposes Russell Brunson's sales funnel and online business content through a searchable RAG (Retrieval-Augmented Generation) system.

## Overview

This server provides AI-powered access to Russell Brunson's expertise in sales funnels, ClickFunnels, online business growth, and marketing strategies through the MCP protocol, enabling Claude and other LLM applications to retrieve and synthesize funnel-building insights.

## Features

- 🎯 **Funnel Expertise**: Access Russell Brunson's proven frameworks for sales funnels and online business
- 🔍 **Smart Search**: Vector-based semantic search across Russell Brunson content transcripts
- 📚 **Citation-Based Answers**: All responses include source references
- 🔐 **Secure API Key Auth**: Production-ready authentication for remote access
- 🚀 **Railway Deployment**: One-click deploy with persistent ChromaDB storage
- ⚡ **Fast Retrieval**: Optimized chunking and embedding strategies

## Tools

### `ask_russell_brunson`
Ask questions about sales funnels, ClickFunnels, online business growth, and Russell Brunson's marketing frameworks.

**Parameters:**
- `question` (required): Your funnel/business question
- `top_k` (optional, default: 18): Number of content chunks to retrieve
- `max_tokens` (optional, default: 2600): Maximum response length
- `user_context` (optional): Additional context to tailor recommendations
- `response_style` (optional): `'concise'`, `'detailed'`, or `'comprehensive'`

**Returns:** `{answer, sources, confidence}`

**Example Questions:**
- "How do I build a perfect webinar funnel?"
- "What's the value ladder framework?"
- "How do I create an irresistible offer?"
- "What funnel should I use for my online course?"
- "How do I scale from $10k to $100k/month?"
- "What's the best ClickFunnels setup for high-ticket coaching?"
- "How do I structure my offer stack for maximum conversions?"

### `about`
Get information about this MCP server and its capabilities.

## Setup

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Add transcripts:**
   Place Russell Brunson transcript `.md` files in `/transcripts/` directory

3. **Set environment variables:**
   ```bash
   export OPENAI_API_KEY=your_openai_key
   ```

4. **Run ingestion:**
   ```bash
   python scripts/ingest.py
   ```

5. **Start MCP server (stdio):**
   ```bash
   python mcp_server.py
   ```

### Railway Deployment

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Ask Russell Brunson MCP"
   git remote add origin https://github.com/YOUR_USERNAME/ask-russell-brunson.git
   git push -u origin main
   ```

2. **Deploy on Railway:**
   - Create new project from GitHub repo
   - Add environment variables:
     - `OPENAI_API_KEY`: Your OpenAI API key
     - `VALID_API_KEYS`: Comma-separated API keys for MCP access
     - `MCP_SERVER_URL`: Your Railway app URL
     - `ENVIRONMENT`: `production`
   - (Optional) Add Railway volume at `/data` for persistent ChromaDB

3. **First deployment:**
   - Railway will build the Docker image
   - Ingestion runs automatically (~10 minutes)
   - Server starts and exposes MCP endpoint

4. **Test the deployment:**
   ```bash
   curl https://your-app.railway.app/health
   ```

## Configuration

### `configs/ask-russell-brunson-deploy.yaml`

Main configuration file for production deployment:

- **knowledge_base**: Creator info and personality (strategic, funnel-focused)
- **data_sources**: Transcript locations and preferences
- **embeddings**: OpenAI embeddings configuration
- **chunking**: Smart chunking for optimal retrieval
- **search**: Hybrid search with MMR diversity
- **generation**: GPT-4o-mini for answer synthesis
- **chroma**: Vector database settings

## Content Format

Transcripts should be Markdown files with optional YAML frontmatter:

```markdown
---
title: "Lesson Title"
channel: "@RussellBrunson"
url: https://youtube.com/watch?v=VIDEO_ID
date_processed: 2025-01-15
---

## Transcript
Full transcript text goes here...
```

## MCP Protocol

This server implements the [Model Context Protocol](https://modelcontextprotocol.io/) for seamless integration with Claude and other LLM applications.

**Remote Access URL:**
```
https://your-app.railway.app/mcp?apiKey=YOUR_API_KEY
```

## Architecture

- **FastMCP**: MCP protocol implementation
- **ChromaDB**: Vector database for embeddings
- **OpenAI**: Embeddings (text-embedding-3-small) + Generation (gpt-4o-mini)
- **FastAPI**: HTTP server for remote access
- **Railway**: Cloud deployment platform

## Topics Covered

- Sales funnel design and optimization
- ClickFunnels platform strategy
- Value ladder framework
- Webinar funnels and automated selling
- Offer creation and value stacking
- Traffic generation strategies
- Product launch frameworks (Expert Secrets, DotCom Secrets)
- Story-driven marketing
- Scaling online businesses
- Community building and customer retention

## Performance

- **Retrieval speed**: < 1 second for most queries
- **Answer generation**: 2-5 seconds (varies by response_style)
- **Database size**: Russell Brunson content transcripts
- **Uptime**: 99%+ on Railway with persistent storage

## License

Private - For authorized use only

## Author

Benjamin Merritt

## Support

For issues or questions, contact: [Your contact info]
