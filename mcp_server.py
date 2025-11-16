#!/usr/bin/env python3
"""
MCP Server for Ask Russell Brunson

Exposes Russell Brunson's sales funnel and online business content as Model Context Protocol tools
for Claude Desktop using the fastmcp library.

Tools:
  - ask_russell_brunson(question, top_k?, max_tokens?, user_context?) -> Markdown answer with Sources
  - about() -> System information
"""

import os
import sys
from typing import List, Dict, Optional, Any
import yaml as __yaml

# Ensure imports from this repo work regardless of cwd
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
try:
    # Ensure relative paths in config.yaml resolve correctly
    os.chdir(REPO_ROOT)
except Exception:
    pass

# Allow per-profile config via environment variable
CONFIG_PATH = os.getenv('WIKI_VAULT_CONFIG', os.path.join(REPO_ROOT, 'config.yaml'))
try:
    with open(CONFIG_PATH, 'r') as __f:
        __CFG = __yaml.safe_load(__f)
except Exception:
    __CFG = {}

# Ensure imported scripts don't print to stdout and break MCP protocol
os.environ['WIKI_VAULT_SILENT'] = '1'

from fastmcp import FastMCP  # type: ignore

# Reuse existing functionality
from lib.query import KnowledgeQuery
from lib.full_notes import FullNotesReader


# MCP server name
PROVIDER_NAME = os.getenv('WIKI_VAULT_MCP_NAME') or "ask-russell-brunson"
mcp = FastMCP(PROVIDER_NAME)


class _Lazy:
    query: Optional[KnowledgeQuery] = None
    notes: Optional[FullNotesReader] = None


def _get_query() -> KnowledgeQuery:
    if _Lazy.query is None:
        _Lazy.query = KnowledgeQuery(config_path=CONFIG_PATH)
    return _Lazy.query


def _get_notes() -> FullNotesReader:
    if _Lazy.notes is None:
        _Lazy.notes = FullNotesReader(config_path=CONFIG_PATH)
    return _Lazy.notes


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _answer_with_openai(question: str, context: str, max_tokens: int = 2000, user_context: Optional[str] = None) -> Optional[str]:
    try:
        import openai as _openai
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or len(api_key) < 10:
            return None
        client = _openai.OpenAI(api_key=api_key)
        system_prompt = """
ROLE: You are a sales funnel and online business strategist specializing in Russell Brunson's frameworks and methodologies. Your expertise covers ClickFunnels, sales funnel architecture, offer creation, traffic strategies, and scaling online businesses using Brunson's proven systems.

EXPERTISE AREAS:
- Sales funnel design and optimization (value ladder, funnel hacking, etc.)
- ClickFunnels platform strategy and implementation
- Offer creation and irresistible offer frameworks
- Traffic generation and paid acquisition strategies
- Webinar funnels and automated selling systems
- Product launch frameworks (Expert Secrets, DotCom Secrets)
- Story-driven marketing and copywriting
- Scaling online businesses and revenue optimization
- Community building and customer retention

TASK: Answer the user's question using only the provided Russell Brunson content excerpts. Match your answer's depth and complexity to the question:
- Tactical questions → Direct, actionable funnel strategies with specific frameworks
- Strategic questions → High-level business growth approaches and funnel architecture
- Technical questions → Platform-specific guidance (ClickFunnels setup, funnel mechanics)
- Vague questions → Ask clarifying questions about their business model, offer, or growth stage

APPROACH:
- Lead with Russell Brunson's proven frameworks and methodologies
- Provide specific funnel structures and conversion strategies
- Include story-driven examples and case studies when available
- Use only information explicitly stated in the context
- Focus on the value ladder concept and funnel architecture
- Emphasize testing, optimization, and customer journey mapping

FORMAT FLEXIBILITY:
Prioritize these elements:
1. Clear funnel strategy or framework (value ladder, webinar funnel, etc.)
2. Specific implementation steps with funnel elements
3. Conversion metrics and optimization opportunities
4. Traffic and scaling considerations
5. Story or case study examples
6. Common pitfalls and troubleshooting

CITATIONS: Reference content naturally in your response. End with a "Sources" section listing content titles (no URLs).

CRITICAL CONSTRAINT: Only use information explicitly stated in the provided Russell Brunson context. Do not make up funnels, invent conversion rates, or add information not present in the sources.

EXAMPLES:

Funnel strategy question: "How do I structure a webinar funnel for my online course?"
Response: Comprehensive breakdown covering the perfect webinar framework, pre-webinar sequence, live presentation structure, offer stack creation, scarcity/urgency elements, follow-up sequences, and conversion optimization tactics. Include specific email sequences and page types from Russell's frameworks.

Offer creation question: "How do I create an irresistible offer that converts?"
Response: Direct explanation of the offer stack framework, value stacking principles, bonus creation strategies, pricing psychology, risk reversal tactics, and guarantee structures. Include Russell's frameworks for positioning and presenting offers to maximize perceived value.

Business growth question: "I'm stuck at $10k/month. How do I scale to $100k/month?"
Response: Strategic roadmap covering value ladder expansion, traffic diversification, funnel optimization, team building considerations, and automation systems. Include specific funnel types for different price points and customer acquisition strategies for scaling.

ClickFunnels question: "What's the best funnel type for selling a high-ticket coaching program?"
Response: Detailed funnel architecture including application funnel structure, qualification process, sales call booking system, follow-up automation, and conversion strategies. Include page types, email sequences, and optimization tactics specific to high-ticket sales.
"""
        user_tailor = (f"\n\nUser context to tailor recommendations: {user_context}" if user_context else "")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context excerpts:\n{context}{user_tailor}"},
            {"role": "user", "content": f"Question: {question}\n\nProvide helpful guidance based only on the context above."},
        ]
        resp = client.chat.completions.create(
            model=os.getenv('WIKI_VAULT_OPENAI_MODEL', 'gpt-4o-mini'),
            messages=messages,
            temperature=0.2,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content
    except Exception:
        return None


def _keywords(text: str) -> list:
    import re as _re
    toks = _re.findall(r"[A-Za-z0-9']+", text.lower())
    return [t for t in toks if len(t) >= 3]


def _rank_hits_by_keyword(question: str, hits: list, k: int) -> list:
    words = set(_keywords(question))
    if not words:
        return hits[:k]
    def score_hit(h: dict) -> float:
        txt = (h.get('content') or '').lower()
        score = sum(txt.count(w) for w in words)
        sim = h.get('score') or 0.0
        return score + sim
    ranked = sorted(hits, key=score_hit, reverse=True)
    seen = set()
    out = []
    for h in ranked:
        key = hash((h.get('content') or '')[:160])
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
        if len(out) >= k:
            break
    return out


def _group_by_source(hits: list, max_sources: int = 5, per_source: int = 1) -> list:
    """Group hits by file_path/title and take top segments per source for diversity."""
    buckets = {}
    order = []
    for h in hits:
        meta = h.get('metadata', {}) or {}
        key = meta.get('file_path') or meta.get('title') or meta.get('source_title')
        if not key:
            key = h.get('id')
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(h)
    selected = []
    for key in order:
        segs = buckets[key][:per_source]
        selected.extend(segs)
        if len(selected) >= max_sources * per_source:
            break
    return selected


@mcp.tool()
def ask_russell_brunson(question: str, top_k: Any = 18, max_tokens: Any = 2600, user_context: Optional[str] = None, response_style: str = 'detailed') -> Dict[str, Any]:
    """Ask questions about sales funnels, ClickFunnels, online business growth, and Russell Brunson's marketing frameworks. Get expert funnel strategy and business scaling guidance. Returns {answer, sources}."""
    q = _get_query()
    k = _to_int(top_k) or 12
    mt = _to_int(max_tokens) or 2000
    # Adjust verbosity based on response_style
    style = (response_style or 'detailed').lower()
    if style == 'concise':
        mt = min(mt, 1200)
    elif style == 'comprehensive':
        mt = max(mt, 3200)
    initial = max(50, k * 5)
    hits = q.search(question, top_k=initial, collection='content')
    # Prefer transcripts
    filtered = [h for h in hits if (h.get('metadata', {}) or {}).get('doc_type') == 'transcript'] or hits
    filtered = _rank_hits_by_keyword(question, filtered, initial)
    # Diversify: take top segments grouped by source
    filtered = _group_by_source(filtered, max_sources=min(6, k//3 + 2), per_source=1)
    # Build context
    seen = set()
    parts = []
    for h in filtered:
        txt = h.get('content') or ''
        if not txt:
            continue
        key = hash(txt[:120])
        if key in seen:
            continue
        seen.add(key)
        meta = h.get('metadata', {}) or {}
        title = meta.get('title') or meta.get('source_title') or 'Untitled'
        section = meta.get('section') or meta.get('concept_name') or ''
        head = f"Source: {title}"
        if section:
            head += f" ({section})"
        parts.append(head + "\n" + txt)
    context = "\n\n---\n".join(parts)
    ans = _answer_with_openai(question, context, max_tokens=mt, user_context=user_context)
    if not ans:
        # Structured fallback
        parts = context.split("\n\n---\n")[:8]
        bullets = "\n\n".join(f"- {p[:300]}" for p in parts)
        ans = (
            f"# Answer (no OpenAI API available)\n\nBased on retrieved Russell Brunson content excerpts.\n\n"
            f"## Key Funnel Strategies\n\n{bullets}\n\n"
            f"## Suggested Next Steps\n\n- Review which funnel framework applies to your business model\n- Implement one Russell Brunson strategy this week (value ladder, offer stack, or webinar funnel)\n- Test and optimize your conversion metrics\n"
        )
    # Build sources list (titles only, no URLs)
    sources = []
    seen_src = set()
    used_scores = []
    for h in filtered:
        meta = h.get('metadata', {}) or {}
        title = meta.get('title') or meta.get('source_title') or 'Untitled'
        url = meta.get('url') or meta.get('source_url')
        fp = meta.get('file_path')
        key = (title, url or fp)
        if key in seen_src:
            continue
        seen_src.add(key)
        sources.append({'title': title, 'url': url})
        if isinstance(h.get('score'), (int, float)):
            used_scores.append(h.get('score'))
        if len(sources) >= 5:
            break
    confidence = round(sum(used_scores)/len(used_scores), 3) if used_scores else None
    return {'answer': ans, 'sources': sources, 'confidence': confidence}


@mcp.tool()
def about() -> Dict[str, Any]:
    """Returns a short description of this MCP provider and how to use it."""
    try:
        import yaml as _yaml
        with open(CONFIG_PATH, 'r') as _f:
            _cfg = _yaml.safe_load(_f)
        kb = _cfg.get('knowledge_base', {})
        return {
            'name': kb.get('name') or 'Ask Russell Brunson KB',
            'purpose': 'Search and get expert sales funnel and business growth advice from Russell Brunson content',
            'topic': kb.get('topic') or 'Sales funnels, online business growth, and marketing strategies',
            'recommended_tools': ['ask_russell_brunson', 'about'],
            'notes': 'Use ask_russell_brunson for questions about sales funnels, ClickFunnels, and online business strategies. Example questions: "How do I build a perfect webinar funnel?", "What\'s the value ladder framework?", "How do I create an irresistible offer?", "What funnel should I use for my online course?", "How do I scale from $10k to $100k/month?". Get comprehensive funnel strategy answers with sources from Russell Brunson\'s content.'
        }
    except Exception:
        return {
            'name': 'Ask Russell Brunson KB',
            'purpose': 'Sales funnel and online business Q&A from Russell Brunson',
            'recommended_tools': ['ask_russell_brunson', 'about'],
            'notes': 'Ask questions about sales funnels, ClickFunnels, offer creation, and online business growth strategies.'
        }


if __name__ == "__main__":
    # Run the MCP server (stdio)
    mcp.run()
