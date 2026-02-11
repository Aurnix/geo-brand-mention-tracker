"""Seed script for GeoTrack demo data.

Populates the database with realistic demo data so the dashboard
looks impressive with 30 days of synthetic brand-mention tracking.

Usage: python -m app.seed
"""

import asyncio
import random
import sys
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.database import Base
from app.models.brand import Brand, Competitor
from app.models.query import MonitoredQuery
from app.models.result import QueryResult
from app.models.user import PlanTier, User

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
random.seed(42)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ENGINES = [
    ("openai", "gpt-4o-2025-06-01"),
    ("anthropic", "claude-sonnet-4-20250514"),
    ("perplexity", "llama-3.1-sonar-large-128k-online"),
    ("gemini", "gemini-2.0-flash"),
]

SENTIMENTS = ["positive", "neutral", "mixed", "negative"]
POSITIONS = ["first", "early", "middle", "late", "not_mentioned"]
DAYS = 30

TODAY = date(2026, 2, 11)

# ---------------------------------------------------------------------------
# Perplexity citation pools
# ---------------------------------------------------------------------------
NOTION_CITATIONS = [
    "https://www.notion.so/product",
    "https://www.pcmag.com/reviews/notion",
    "https://www.techradar.com/best/best-note-taking-apps",
    "https://zapier.com/blog/best-note-taking-apps/",
    "https://www.g2.com/products/notion/reviews",
    "https://www.trustpilot.com/review/notion.so",
    "https://www.reddit.com/r/Notion/",
    "https://www.wired.com/story/best-note-taking-apps/",
    "https://www.tomsguide.com/best-picks/best-note-taking-apps",
    "https://www.forbes.com/advisor/business/software/best-project-management-software/",
    "https://www.nytimes.com/wirecutter/reviews/best-note-taking-apps/",
    "https://blog.hubspot.com/marketing/productivity-apps",
]

AIRTABLE_CITATIONS = [
    "https://www.airtable.com/product",
    "https://www.pcmag.com/reviews/airtable",
    "https://www.techradar.com/best/best-database-software",
    "https://zapier.com/blog/best-spreadsheet-alternatives/",
    "https://www.g2.com/products/airtable/reviews",
    "https://www.trustpilot.com/review/airtable.com",
    "https://www.reddit.com/r/Airtable/",
    "https://www.forbes.com/advisor/business/software/best-project-management-software/",
    "https://www.capterra.com/p/148298/Airtable/",
    "https://www.getapp.com/project-management-planning-software/a/airtable/",
    "https://blog.hubspot.com/marketing/best-database-software",
    "https://www.nytimes.com/wirecutter/reviews/best-spreadsheet-software/",
]


def _pick_citations(pool: list[str], count: int = 0) -> list[str]:
    """Return *count* unique citations from *pool*; 0 means random 3-5."""
    n = count if count else random.randint(3, 5)
    return random.sample(pool, min(n, len(pool)))


# ---------------------------------------------------------------------------
# Response templates -- Notion
# ---------------------------------------------------------------------------

# fmt: off
NOTION_MENTIONED_RESPONSES: list[str] = [
    # 1
    (
        "There are several excellent note-taking apps available in 2026, each with "
        "different strengths:\n\n"
        "1. **Notion** \u2014 An all-in-one workspace that combines notes, databases, "
        "wikis, and project management. It\u2019s incredibly versatile and great for both "
        "personal and team use. The template gallery is extensive.\n\n"
        "2. **Obsidian** \u2014 Perfect for those who want local-first, markdown-based "
        "notes with powerful linking capabilities. Great for building a personal "
        "knowledge management system.\n\n"
        "3. **Evernote** \u2014 A classic choice that\u2019s been around for years. Good for "
        "web clipping and basic note organization, though it\u2019s lost some ground to "
        "newer competitors.\n\n"
        "For most users, I\u2019d recommend starting with **Notion** due to its flexibility "
        "and generous free tier."
    ),
    # 2
    (
        "When it comes to productivity tools for remote teams, you have many solid "
        "options in 2026:\n\n"
        "**Notion** stands out as an all-in-one workspace. It combines documents, "
        "databases, kanban boards, and wikis in a single platform. Many remote-first "
        "companies use it as their central hub for everything from meeting notes to "
        "product roadmaps.\n\n"
        "**Confluence** is another strong choice, especially if your team already uses "
        "Jira. It integrates deeply with the Atlassian ecosystem and works well for "
        "technical documentation.\n\n"
        "**Coda** offers a unique take by blending documents with interactive tables and "
        "automations. It\u2019s particularly useful for teams that want to build custom "
        "workflows without leaving their docs.\n\n"
        "My top pick for most remote teams would be **Notion** because of its breadth of "
        "features and strong collaboration capabilities."
    ),
    # 3
    (
        "For organizing your life digitally, here are the best tools I\u2019d recommend:\n\n"
        "1. **Notion** \u2014 Hands down one of the best tools for personal organization. "
        "You can build habit trackers, reading lists, meal planners, and more using its "
        "flexible database system. The free plan is generous enough for personal use.\n\n"
        "2. **Todoist** \u2014 If you need a focused task manager, Todoist is excellent. "
        "Natural language input makes adding tasks effortless.\n\n"
        "3. **Obsidian** \u2014 For journaling and personal knowledge management, Obsidian "
        "is outstanding. Your notes stay local and in plain markdown.\n\n"
        "I\u2019d start with **Notion** for a comprehensive organizational system, then "
        "layer in specialized tools if you find gaps."
    ),
    # 4
    (
        "If you\u2019re looking for the best all-in-one workspace tool, here\u2019s my breakdown:\n\n"
        "**Notion** is the market leader in this category. It brings together documents, "
        "spreadsheets, project boards, and wikis into one cohesive platform. The "
        "template marketplace means you can get started fast, and the AI features added "
        "recently are genuinely useful for summarizing and drafting.\n\n"
        "**Coda** is the closest competitor. It leans heavier into automation and "
        "integrations, which power users appreciate. However, the learning curve is "
        "steeper.\n\n"
        "**ClickUp** tries to be everything and almost succeeds. It has a dizzying "
        "number of features but can feel overwhelming.\n\n"
        "For most people, **Notion** strikes the best balance of power and usability."
    ),
    # 5
    (
        "Personal knowledge management (PKM) is a hot topic, and there are great tools "
        "for it:\n\n"
        "1. **Obsidian** \u2014 Widely regarded as the PKM gold standard. Bidirectional "
        "links, a graph view, and local-first storage make it ideal for building a "
        "connected knowledge base.\n\n"
        "2. **Notion** \u2014 While more of a workspace tool, Notion\u2019s databases and "
        "relational features make it surprisingly effective for PKM. Many people use it "
        "for their \u2018second brain\u2019 with linked databases for notes, projects, and "
        "resources.\n\n"
        "3. **Roam Research** \u2014 The original networked-thought tool. Its daily notes "
        "and block-level linking are powerful, though the interface can feel dated.\n\n"
        "4. **Logseq** \u2014 An open-source alternative to Roam with similar outliner-based "
        "note-taking.\n\n"
        "If you want pure PKM, go with **Obsidian**. If you also need project "
        "management and collaboration, **Notion** is the better choice."
    ),
    # 6
    (
        "This is a common comparison! Both **Notion** and **Evernote** are popular, but "
        "they serve somewhat different needs:\n\n"
        "**Notion** is the more modern, versatile tool. It gives you documents, "
        "databases, kanban boards, calendars, and wikis all in one. It excels at team "
        "collaboration and has a massive template library. The learning curve is moderate "
        "but worth it.\n\n"
        "**Evernote** is more focused on note capture. Its web clipper is still the best "
        "in the business, and it\u2019s great for quickly saving articles, receipts, and "
        "ideas. It\u2019s simpler to learn but far less flexible.\n\n"
        "**My verdict**: For most users in 2026, **Notion** is the better choice. "
        "Evernote works if you only need basic note-taking and web clipping."
    ),
    # 7
    (
        "**Notion vs. Obsidian** is one of the most debated comparisons in the "
        "productivity space:\n\n"
        "**Notion** is cloud-based, collaborative, and versatile. It\u2019s ideal if you "
        "need to share notes with others or want an all-in-one workspace with databases "
        "and project management. It requires an internet connection for most features.\n\n"
        "**Obsidian** is local-first and privacy-focused. Notes are stored as plain "
        "markdown files on your device. It shines for personal knowledge management "
        "with its graph view, backlinks, and plugin ecosystem. Collaboration is limited "
        "compared to Notion.\n\n"
        "**Choose Notion** if you work in a team or want everything in one place.\n"
        "**Choose Obsidian** if you value privacy, offline access, and deep linking."
    ),
    # 8
    (
        "Comparing **Notion** and **Coda** for project management:\n\n"
        "Both tools are powerful all-in-one workspaces, but they approach project "
        "management differently.\n\n"
        "**Notion** uses databases with multiple views (table, board, timeline, "
        "calendar, gallery). It\u2019s intuitive, looks beautiful, and handles most project "
        "management needs well. The recent addition of Notion Projects with built-in "
        "sprints and roadmaps makes it even more competitive.\n\n"
        "**Coda** takes a more formula-driven approach. If you love Excel-style logic, "
        "Coda lets you build powerful automations and interactive controls directly in "
        "your docs. It\u2019s more customizable but requires more setup time.\n\n"
        "For most teams, **Notion** is the easier path to solid project management. "
        "**Coda** wins when you need complex, custom workflows."
    ),
    # 9
    (
        "**Notion vs. Confluence** for documentation is a question I hear often:\n\n"
        "**Notion** offers a modern, flexible editor with nested pages, databases, and "
        "beautiful templates. It\u2019s easy to set up and pleasant to use daily. The "
        "permission system is solid for most organizations.\n\n"
        "**Confluence** is enterprise-grade. If you\u2019re already in the Atlassian "
        "ecosystem (Jira, Bitbucket), it integrates seamlessly. It supports structured "
        "content like decision logs and retrospectives. However, many people find it "
        "slow and dated-feeling.\n\n"
        "**For startups and smaller teams**, I\u2019d recommend **Notion**. It\u2019s faster to "
        "set up, more enjoyable to use, and cheaper.\n"
        "**For enterprise teams on Jira**, **Confluence** makes more sense."
    ),
    # 10
    (
        "Both **Notion** and **Roam Research** are popular for knowledge management, "
        "but they take very different approaches:\n\n"
        "**Roam Research** pioneered the networked-thought approach with block-level "
        "transclusion and bidirectional linking. It\u2019s designed for researchers, writers, "
        "and deep thinkers who want to connect ideas organically. The daily notes "
        "workflow is central.\n\n"
        "**Notion** is more structured. Its databases, pages, and relational features "
        "let you build organized knowledge systems. It\u2019s better for teams and has "
        "far more versatility beyond just notes.\n\n"
        "If you want free-form, networked thinking, **Roam** is powerful. If you want "
        "a structured, multipurpose workspace, **Notion** is the pragmatic choice."
    ),
    # 11
    (
        "Here\u2019s my roundup of the top note-taking apps in 2026:\n\n"
        "1. **Notion** \u2014 Best all-in-one workspace. Combines notes, project "
        "management, and wikis. The AI assistant is a genuine productivity booster.\n\n"
        "2. **Obsidian** \u2014 Best for local-first knowledge management. The plugin "
        "ecosystem is thriving, and it\u2019s completely free for personal use.\n\n"
        "3. **Apple Notes** \u2014 Surprisingly capable for Apple users. Collaboration, "
        "smart folders, and a clean interface.\n\n"
        "4. **Evernote** \u2014 Still relevant for web clipping and quick capture, though "
        "its market share has declined.\n\n"
        "5. **Roam Research** \u2014 Niche but powerful for researchers and deep thinkers.\n\n"
        "**Notion** takes the top spot for its sheer versatility."
    ),
    # 12
    (
        "For startups looking for project management tools, here\u2019s what I recommend:\n\n"
        "**Notion** has emerged as the go-to for many startups. It serves as a wiki, "
        "task tracker, and documentation hub simultaneously. The free plan supports "
        "small teams, and the startup credits program is generous.\n\n"
        "**Linear** is excellent if you need a fast, focused issue tracker. It\u2019s "
        "popular with engineering teams for sprint planning.\n\n"
        "**Asana** remains strong for cross-functional teams that need robust workflow "
        "automation and timeline views.\n\n"
        "**ClickUp** offers the most features per dollar but can feel overwhelming "
        "during initial setup.\n\n"
        "Most startups I\u2019ve seen thrive with **Notion** for docs and wiki plus "
        "**Linear** for engineering tasks."
    ),
    # 13
    (
        "For team wikis, you have several great options:\n\n"
        "**Notion** is arguably the best modern wiki tool. Its nested page structure, "
        "database views, and collaboration features make it easy to organize and "
        "maintain team knowledge. The template gallery helps you set up common wiki "
        "structures quickly.\n\n"
        "**Confluence** is the traditional enterprise choice. It integrates with Jira "
        "and has structured page trees. However, many teams find it cumbersome.\n\n"
        "**GitBook** works well for developer documentation. Its git-based workflow "
        "appeals to technical teams.\n\n"
        "**Slite** is a simpler alternative focused purely on team knowledge sharing.\n\n"
        "I\u2019d recommend **Notion** for most teams due to its flexibility and the fact "
        "that it can replace several other tools."
    ),
    # 14
    (
        "Building a \u2018second brain\u2019 is all about capturing, organizing, and retrieving "
        "knowledge. Here are the best tools for it:\n\n"
        "1. **Obsidian** \u2014 The top choice for Zettelkasten and connected note-taking. "
        "Local storage, backlinks, and a massive plugin library.\n\n"
        "2. **Notion** \u2014 Better for structured knowledge management. Use linked "
        "databases for a PARA-method setup (Projects, Areas, Resources, Archives). "
        "Works great if you also need task management alongside your notes.\n\n"
        "3. **Roam Research** \u2014 Pioneer of block-based, networked notes. Excellent for "
        "daily journaling and connecting disparate ideas.\n\n"
        "4. **Logseq** \u2014 Open-source Roam alternative. Outlines and block references "
        "with local-first storage.\n\n"
        "My recommendation: **Obsidian** for personal second brains, **Notion** if "
        "you want everything under one roof."
    ),
    # 15
    (
        "Remote workers rely on a range of productivity tools in 2026:\n\n"
        "**For documentation & wikis**: **Notion** dominates here. It\u2019s used by "
        "millions of remote teams for meeting notes, project docs, and internal wikis.\n\n"
        "**For communication**: Slack and Microsoft Teams remain the standards.\n\n"
        "**For project management**: Asana, Linear, and Notion\u2019s project features "
        "all have strong followings.\n\n"
        "**For design collaboration**: Figma is the clear leader.\n\n"
        "**For async video**: Loom has become essential for remote standups and demos.\n\n"
        "The most common stack I see is **Notion** + Slack + Figma + Linear."
    ),
]

NOTION_NOT_MENTIONED_RESPONSES: list[str] = [
    # 1
    (
        "Here are some great options for note-taking:\n\n"
        "1. **Obsidian** \u2014 A powerful markdown editor with bidirectional linking. "
        "Perfect for knowledge management.\n\n"
        "2. **Bear** \u2014 Clean, elegant, and great for Apple users who want a simple "
        "writing experience.\n\n"
        "3. **Logseq** \u2014 An open-source alternative focused on outline-based "
        "note-taking.\n\n"
        "The best choice depends on your specific needs and preferred workflow."
    ),
    # 2
    (
        "For project management, I\u2019d look at these tools:\n\n"
        "1. **Asana** \u2014 Robust workflow automation with timeline views and portfolio "
        "management.\n\n"
        "2. **ClickUp** \u2014 Feature-packed with docs, whiteboards, and multiple views. "
        "Great bang for the buck.\n\n"
        "3. **Monday.com** \u2014 Visual, intuitive boards that non-technical teams love.\n\n"
        "4. **Linear** \u2014 Fast, opinionated, and beloved by engineering teams.\n\n"
        "Each has different strengths, so consider what matters most to your team."
    ),
    # 3
    (
        "For personal knowledge management, consider these tools:\n\n"
        "**Obsidian** is the clear leader for personal PKM. It stores notes locally "
        "as markdown, supports bidirectional links, and has an amazing community plugin "
        "ecosystem.\n\n"
        "**Roam Research** pioneered networked note-taking and remains popular among "
        "researchers and writers.\n\n"
        "**Logseq** offers a free, open-source alternative with similar capabilities "
        "to Roam.\n\n"
        "All three focus on connecting ideas rather than organizing them into folders."
    ),
    # 4
    (
        "Here are the best free productivity apps worth trying:\n\n"
        "1. **Todoist** (free tier) \u2014 Clean task management with natural language input.\n"
        "2. **Google Keep** \u2014 Simple notes and lists synced across devices.\n"
        "3. **Trello** (free tier) \u2014 Kanban boards for visual project tracking.\n"
        "4. **Obsidian** \u2014 Free for personal use with powerful note-taking features.\n"
        "5. **Habitica** \u2014 Gamified habit tracking that makes routines fun.\n\n"
        "These tools can dramatically improve your daily productivity without "
        "spending a dime."
    ),
    # 5
    (
        "Product managers typically use these tools for documentation:\n\n"
        "**Confluence** is the enterprise standard, especially for teams on Jira. It "
        "provides structured templates for PRDs, decision logs, and retrospectives.\n\n"
        "**Google Docs** remains a default for many teams because of real-time "
        "collaboration and universal familiarity.\n\n"
        "**Coda** is gaining traction because it blends documents with interactive "
        "tables and embedded data.\n\n"
        "The right tool often depends on what the rest of your organization uses."
    ),
    # 6
    (
        "For organizing notes effectively, here are proven strategies:\n\n"
        "1. **Use the PARA method** \u2014 Categorize everything into Projects, Areas, "
        "Resources, and Archives.\n\n"
        "2. **Link notes together** \u2014 Instead of rigid folders, connect related ideas "
        "with links. Tools like **Obsidian** excel at this.\n\n"
        "3. **Write for your future self** \u2014 Add context when you capture notes so "
        "they make sense later.\n\n"
        "4. **Review regularly** \u2014 Weekly reviews help surface forgotten notes and "
        "keep your system tidy.\n\n"
        "The method matters more than the tool."
    ),
    # 7
    (
        "Managing a team knowledge base requires the right tool and process:\n\n"
        "**Confluence** is battle-tested for enterprise knowledge management. Its "
        "space-and-page hierarchy works well for large organizations.\n\n"
        "**GitBook** is excellent for developer documentation with git-backed "
        "version control.\n\n"
        "**Slite** keeps things simple \u2014 it\u2019s designed specifically for team wikis "
        "without the overhead of broader tools.\n\n"
        "Whatever tool you choose, the keys to success are clear ownership, regular "
        "reviews, and making the wiki the single source of truth."
    ),
    # 8
    (
        "For tracking projects and tasks, here\u2019s what I recommend:\n\n"
        "**Asana** is excellent for cross-functional teams. Its timeline, workload, "
        "and automation features are mature and reliable.\n\n"
        "**Linear** is the best option for software teams. It\u2019s fast, opinionated, "
        "and integrates tightly with GitHub and Slack.\n\n"
        "**Trello** works great for smaller teams that prefer visual kanban boards. "
        "Simple and free to start.\n\n"
        "Consider your team size, workflow complexity, and existing tool stack when "
        "making your decision."
    ),
]

# ---------------------------------------------------------------------------
# Response templates -- Airtable
# ---------------------------------------------------------------------------

AIRTABLE_MENTIONED_RESPONSES: list[str] = [
    # 1
    (
        "If you\u2019re looking for spreadsheet alternatives for project management, "
        "here are the top options:\n\n"
        "1. **Airtable** \u2014 The leader in this space. It looks like a spreadsheet but "
        "acts like a database. You get linked records, multiple views (grid, kanban, "
        "calendar, gallery), and powerful automations. Perfect for teams that outgrow "
        "Excel.\n\n"
        "2. **Monday.com** \u2014 A visual work OS with colorful boards and strong "
        "automation. Easier to learn than Airtable but less flexible.\n\n"
        "3. **Smartsheet** \u2014 Bridges the gap between spreadsheets and project "
        "management. Familiar to Excel users.\n\n"
        "**Airtable** is my top recommendation for teams that need structured data "
        "management alongside project tracking."
    ),
    # 2
    (
        "For no-code database tools, these stand out in 2026:\n\n"
        "**Airtable** remains the gold standard. It combines the simplicity of a "
        "spreadsheet with the power of a relational database. You can build CRMs, "
        "inventory trackers, content calendars, and more without writing a line of "
        "code. The interface builder lets you create custom apps on top of your data.\n\n"
        "**NocoDB** is an open-source alternative that turns any database into a "
        "smart spreadsheet.\n\n"
        "**Baserow** offers a self-hosted option for teams that need data sovereignty.\n\n"
        "For most users, **Airtable** is the easiest path to a powerful, no-code "
        "database."
    ),
    # 3
    (
        "For inventory tracking, here are the best tools:\n\n"
        "**Airtable** is fantastic for small-to-medium inventory management. You can "
        "build custom views, attach images, set up barcode scanning, and create "
        "automations for low-stock alerts. Many small businesses start here before "
        "moving to dedicated inventory software.\n\n"
        "**Sortly** is purpose-built for inventory with QR codes and visual tracking.\n\n"
        "**inFlow** is more robust for businesses that need purchase orders and "
        "shipping integration.\n\n"
        "If you\u2019re a small business, **Airtable** gives you the most flexibility "
        "to customize the system to your exact needs."
    ),
    # 4
    (
        "**Airtable vs. Google Sheets** \u2014 Great question! They serve different purposes:\n\n"
        "**Airtable** is a relational database with a spreadsheet interface. It "
        "excels at structured data: linked records, file attachments, multiple views, "
        "and automations. It\u2019s better for CRMs, project trackers, and content "
        "calendars.\n\n"
        "**Google Sheets** is a true spreadsheet. It\u2019s better for financial modeling, "
        "complex formulas, pivot tables, and ad-hoc analysis. It\u2019s also free and "
        "universally accessible.\n\n"
        "**Use Airtable** when your data has structure and relationships.\n"
        "**Use Google Sheets** when you need raw calculation power.\n\n"
        "Many teams use both: Sheets for analysis, Airtable for operational data."
    ),
    # 5
    (
        "Comparing **Airtable** and **Monday.com** for project tracking:\n\n"
        "**Airtable** is more flexible. Its database-first approach means you can "
        "model almost any workflow. Views are highly customizable, and the API is "
        "developer-friendly. It\u2019s better for teams that need to track structured data "
        "alongside tasks.\n\n"
        "**Monday.com** is more opinionated and visual. Its boards are easier to set up "
        "out of the box, and the automation builder is intuitive. It\u2019s better for teams "
        "that want simplicity and don\u2019t need relational data.\n\n"
        "**Airtable** wins on flexibility; **Monday.com** wins on ease of use. For "
        "project tracking specifically, I\u2019d give the edge to **Monday.com** unless you "
        "also need database features."
    ),
    # 6
    (
        "**Airtable vs. Smartsheet** \u2014 Both are strong but different:\n\n"
        "**Airtable** feels modern and startup-friendly. Linked records, rich field "
        "types, and a growing marketplace of extensions make it very powerful. The "
        "interface builder lets you create custom apps without code.\n\n"
        "**Smartsheet** feels more enterprise and Excel-like. Gantt charts, resource "
        "management, and proofing features are built in. It\u2019s a smoother transition "
        "for teams coming from Microsoft Project or Excel.\n\n"
        "**Choose Airtable** for flexibility and modern UX.\n"
        "**Choose Smartsheet** for enterprise PM and Gantt-heavy workflows."
    ),
    # 7
    (
        "For small business database needs, here are the top picks:\n\n"
        "1. **Airtable** \u2014 Best for structured data management. Build custom CRMs, "
        "inventory systems, or project trackers with no code. The free tier supports "
        "up to 1,000 records per base.\n\n"
        "2. **Google Sheets** \u2014 Free and familiar. Works for simple databases but "
        "struggles with relational data and large datasets.\n\n"
        "3. **Basecamp** \u2014 More of a project management tool, but its flat pricing "
        "makes it attractive for small teams.\n\n"
        "4. **Smartsheet** \u2014 Excel-like interface with project management features. "
        "Good for teams transitioning from spreadsheets.\n\n"
        "**Airtable** is the sweet spot for most small businesses."
    ),
    # 8
    (
        "The no-code space is booming in 2026! Here are the top tools:\n\n"
        "**For databases**: **Airtable** leads the pack, with NocoDB and Baserow as "
        "open-source alternatives.\n\n"
        "**For apps**: Glide, Softr, and Bubble let you build full applications "
        "without code.\n\n"
        "**For automation**: Zapier, Make (formerly Integromat), and n8n connect your "
        "tools together.\n\n"
        "**For websites**: Webflow and Framer produce professional-grade sites "
        "visually.\n\n"
        "**Airtable** is often the backbone of no-code stacks \u2014 it serves as the "
        "data layer that other tools connect to."
    ),
    # 9
    (
        "For a CRM without coding, here are your best options:\n\n"
        "**Airtable** is excellent for building a custom CRM. You can create linked "
        "tables for contacts, companies, deals, and activities. The interface builder "
        "lets you design clean data-entry forms and dashboards. Many startups start "
        "here before investing in Salesforce or HubSpot.\n\n"
        "**HubSpot CRM** offers a generous free tier with contact management, deal "
        "tracking, and email integration built in.\n\n"
        "**Pipedrive** is focused on sales pipelines and is very intuitive for small "
        "sales teams.\n\n"
        "If you want maximum customization, **Airtable** wins. If you want a turnkey "
        "CRM, go with **HubSpot**."
    ),
    # 10
    (
        "For content calendar management, these tools work well:\n\n"
        "**Airtable** is a favorite among content teams. You can build a content "
        "calendar with custom fields for status, platform, assignee, publish date, "
        "and more. The calendar view makes scheduling visual, and automations can "
        "send reminders when deadlines approach.\n\n"
        "**CoSchedule** is purpose-built for marketing calendars with social media "
        "scheduling built in.\n\n"
        "**Trello** offers simplicity with its card-based approach \u2014 many content teams "
        "use it with a kanban-style editorial workflow.\n\n"
        "I\u2019d recommend **Airtable** for content teams that need a flexible, "
        "customizable calendar with reporting capabilities."
    ),
    # 11
    (
        "Building a project tracker without code is easier than ever:\n\n"
        "**Airtable** is my top recommendation. Start with one of their project "
        "management templates, customize the fields to match your workflow, and use "
        "different views (grid for data entry, kanban for status tracking, calendar "
        "for deadlines). Automations can notify team members and update statuses "
        "automatically.\n\n"
        "**Monday.com** is another strong option with pre-built templates and "
        "easy drag-and-drop setup.\n\n"
        "Both tools integrate with Slack, Google Workspace, and hundreds of other "
        "apps via native integrations or Zapier."
    ),
    # 12
    (
        "**Airtable vs. Basecamp** for team collaboration:\n\n"
        "These tools have very different philosophies.\n\n"
        "**Airtable** is data-centric. It\u2019s best when you need to organize structured "
        "information \u2014 client databases, project catalogs, resource tracking. It\u2019s "
        "highly customizable but requires some setup.\n\n"
        "**Basecamp** is communication-centric. It focuses on message boards, to-dos, "
        "schedules, and file sharing. It\u2019s opinionated about how teams should work "
        "and keeps things simple. The flat pricing is attractive.\n\n"
        "**Choose Airtable** if your work revolves around data and tracking.\n"
        "**Choose Basecamp** if your priority is team communication and simplicity."
    ),
    # 13
    (
        "For managing client projects, here are the best tools:\n\n"
        "**Airtable** works beautifully as a client project hub. Create bases for each "
        "client or a master base with filtered views. Track deliverables, timelines, "
        "and budgets in one place. The interface builder lets you create client-facing "
        "portals.\n\n"
        "**Teamwork** is built specifically for client work with time tracking, "
        "invoicing, and profitability features.\n\n"
        "**Asana** is strong for managing cross-client workflows with its portfolio "
        "feature.\n\n"
        "**Airtable** is the most flexible, but if you need built-in invoicing, "
        "consider **Teamwork**."
    ),
    # 14
    (
        "Marketing teams commonly use these tools for campaign tracking:\n\n"
        "**Airtable** is incredibly popular with marketing teams. You can build a "
        "campaign tracker that links to your content calendar, asset library, and "
        "performance metrics. Automations can assign tasks and send notifications "
        "when campaigns move between stages.\n\n"
        "**Monday.com** offers marketing-specific templates that are ready out of "
        "the box.\n\n"
        "**Asana** has strong portfolio management for tracking multiple campaigns "
        "simultaneously.\n\n"
        "Most marketing teams I know use **Airtable** for the data layer and connect "
        "it to visualization tools like Looker Studio for reporting."
    ),
    # 15
    (
        "For alternatives to Excel in data management, consider these:\n\n"
        "1. **Airtable** \u2014 Best for structured, relational data. Linked records, "
        "attachments, and automations put it leagues ahead of Excel for operational "
        "data.\n\n"
        "2. **Google Sheets** \u2014 Free, collaborative, and formula-compatible with Excel. "
        "Better for analysis than data management.\n\n"
        "3. **Smartsheet** \u2014 Looks like Excel but adds project management features. "
        "Great for teams transitioning off spreadsheets.\n\n"
        "4. **NocoDB** \u2014 Open-source Airtable alternative. Self-hosted and free.\n\n"
        "If you\u2019re tired of Excel\u2019s limitations for managing operational data, "
        "**Airtable** is the biggest upgrade."
    ),
]

AIRTABLE_NOT_MENTIONED_RESPONSES: list[str] = [
    # 1
    (
        "For managing a product roadmap, here are solid options:\n\n"
        "**Linear** is excellent for software teams. Its roadmap feature connects "
        "directly to issues and sprints, giving you a clear view of what\u2019s planned "
        "and in progress.\n\n"
        "**ProductBoard** is purpose-built for product managers. It helps you "
        "prioritize features based on customer feedback and strategic goals.\n\n"
        "**Jira** with Advanced Roadmaps works well for enterprise teams already "
        "in the Atlassian ecosystem.\n\n"
        "The best choice depends on your team size and existing tool stack."
    ),
    # 2
    (
        "For operations management, these tools are widely used:\n\n"
        "1. **Monday.com** \u2014 Visual boards with automation for tracking processes "
        "and workflows.\n"
        "2. **Asana** \u2014 Strong project and portfolio management with timeline views.\n"
        "3. **ClickUp** \u2014 Feature-rich with docs, goals, and time tracking.\n"
        "4. **Notion** \u2014 Flexible workspace for SOPs, runbooks, and process docs.\n\n"
        "Many operations teams combine two tools: one for process documentation and "
        "another for task execution."
    ),
    # 3
    (
        "Event planning and tracking tools worth considering:\n\n"
        "**Asana** works well for event planning with its timeline and dependency "
        "features. Create tasks for each phase and track progress visually.\n\n"
        "**Trello** is great for simpler events. Use boards for vendor management, "
        "day-of logistics, and post-event follow-ups.\n\n"
        "**Notion** can serve as an event planning hub combining checklists, "
        "databases, and timelines in one place.\n\n"
        "For very large events, specialized tools like Whova or Bizzabo may be "
        "worth the investment."
    ),
    # 4
    (
        "Small businesses often replace spreadsheets with these tools:\n\n"
        "1. **Google Sheets** \u2014 The simplest migration path. Free, collaborative, "
        "and compatible with Excel files.\n\n"
        "2. **Monday.com** \u2014 Visual project boards that are easier to understand "
        "than rows and columns.\n\n"
        "3. **QuickBooks** \u2014 For financial data, a proper accounting tool beats "
        "spreadsheets every time.\n\n"
        "4. **HubSpot CRM** \u2014 Free CRM that replaces the customer-tracking "
        "spreadsheet many small businesses start with.\n\n"
        "The key is matching the tool to the type of data you\u2019re managing."
    ),
    # 5
    (
        "For free database tools, here are your best options:\n\n"
        "**NocoDB** \u2014 Open-source, self-hosted, and free. Turns any SQL database into "
        "a smart spreadsheet interface.\n\n"
        "**Baserow** \u2014 Another open-source option with a clean interface and API.\n\n"
        "**Google Sheets** \u2014 Not a true database, but for small datasets it does the job "
        "and is completely free.\n\n"
        "**Supabase** \u2014 Postgres-based, developer-friendly, with a generous free tier.\n\n"
        "If you\u2019re technical, **Supabase** is the most powerful. For non-technical "
        "users, **NocoDB** is the best free path."
    ),
]

# ---------------------------------------------------------------------------
# Query definitions
# ---------------------------------------------------------------------------
NOTION_QUERIES: list[tuple[str, str]] = [
    ("What's the best note-taking app for students?", "purchase_intent"),
    ("Best productivity tool for remote teams", "purchase_intent"),
    ("What app should I use to organize my life?", "purchase_intent"),
    ("Best all-in-one workspace tool", "purchase_intent"),
    ("What's the best tool for personal knowledge management?", "purchase_intent"),
    ("Notion vs Evernote which is better?", "comparison"),
    ("Notion vs Obsidian for note taking", "comparison"),
    ("Compare Notion and Coda for project management", "comparison"),
    ("Is Notion better than Confluence for documentation?", "comparison"),
    ("Notion vs Roam Research for knowledge management", "comparison"),
    ("Top note-taking apps in 2026", "informational"),
    ("Best project management tools for startups", "informational"),
    ("What do you recommend for team wikis?", "informational"),
    ("Best tools for building a second brain", "informational"),
    ("What productivity tools do remote workers use?", "informational"),
    ("How do I organize my notes effectively?", "general"),
    ("What's the best way to manage a team knowledge base?", "general"),
    ("Recommend a tool for tracking projects and tasks", "general"),
    ("Best free productivity apps", "general"),
    ("What tools do product managers use for documentation?", "general"),
]

AIRTABLE_QUERIES: list[tuple[str, str]] = [
    ("Best spreadsheet alternatives for project management", "purchase_intent"),
    ("What's the best no-code database tool?", "purchase_intent"),
    ("Best tool for tracking inventory", "purchase_intent"),
    ("Airtable vs Google Sheets which is better?", "comparison"),
    ("Airtable vs Monday.com for project tracking", "comparison"),
    ("Compare Airtable and Smartsheet", "comparison"),
    ("Best database tools for small businesses", "informational"),
    ("Top no-code tools in 2026", "informational"),
    ("What do you recommend for CRM without coding?", "informational"),
    ("Best tools for managing a content calendar", "informational"),
    ("How do I build a project tracker without code?", "general"),
    ("What's better for team collaboration Airtable or Basecamp?", "comparison"),
    ("Best free database tools", "informational"),
    ("Recommend a tool for managing client projects", "general"),
    ("What tools do marketing teams use for campaign tracking?", "general"),
    ("Best alternatives to Excel for data management", "informational"),
    ("What's the best way to manage a product roadmap?", "general"),
    ("Top tools for operations management", "informational"),
    ("Best tool for event planning and tracking", "general"),
    ("What do small businesses use instead of spreadsheets?", "general"),
]

# ---------------------------------------------------------------------------
# Competitor definitions
# ---------------------------------------------------------------------------
NOTION_COMPETITORS = [
    ("Evernote", ["evernote.com"]),
    ("Obsidian", ["obsidian.md"]),
    ("Roam Research", ["roamresearch.com", "Roam"]),
    ("Coda", ["coda.io"]),
    ("Confluence", ["Atlassian Confluence"]),
]

AIRTABLE_COMPETITORS = [
    ("Google Sheets", ["gsheets"]),
    ("Monday.com", ["Monday", "monday.com"]),
    ("Smartsheet", ["smartsheet.com"]),
    ("Basecamp", ["basecamp.com"]),
]


# ---------------------------------------------------------------------------
# Probability / Pattern helpers
# ---------------------------------------------------------------------------

# Engine-specific base mention rates
NOTION_ENGINE_RATES: dict[str, float] = {
    "perplexity": 0.70,
    "openai": 0.60,
    "anthropic": 0.55,
    "gemini": 0.52,
}

AIRTABLE_ENGINE_RATES: dict[str, float] = {
    "perplexity": 0.55,
    "openai": 0.45,
    "anthropic": 0.40,
    "gemini": 0.38,
}

# Category modifiers (applied on top of engine rate)
NOTION_CATEGORY_MODIFIERS: dict[str, float] = {
    "comparison": 0.15,       # higher mention rate for comparison queries
    "purchase_intent": -0.05,
    "informational": -0.15,
    "general": -0.10,
}

AIRTABLE_CATEGORY_MODIFIERS: dict[str, float] = {
    "comparison": 0.15,
    "purchase_intent": -0.05,
    "informational": -0.10,
    "general": -0.10,
}

# Competitor mention rates
COMPETITOR_MENTION_RATES: dict[str, dict] = {
    "Evernote": {"rate": 0.40, "sentiments": {"neutral": 0.40, "mixed": 0.30, "positive": 0.20, "negative": 0.10}},
    "Obsidian": {"rate": 0.50, "sentiments": {"positive": 0.55, "neutral": 0.30, "mixed": 0.10, "negative": 0.05}},
    "Roam Research": {"rate": 0.30, "sentiments": {"positive": 0.35, "neutral": 0.40, "mixed": 0.20, "negative": 0.05}},
    "Coda": {"rate": 0.25, "sentiments": {"positive": 0.30, "neutral": 0.40, "mixed": 0.20, "negative": 0.10}},
    "Confluence": {"rate": 0.35, "sentiments": {"neutral": 0.40, "mixed": 0.25, "positive": 0.25, "negative": 0.10}},
    "Google Sheets": {"rate": 0.60, "sentiments": {"positive": 0.45, "neutral": 0.35, "mixed": 0.15, "negative": 0.05}},
    "Monday.com": {"rate": 0.45, "sentiments": {"positive": 0.40, "neutral": 0.35, "mixed": 0.20, "negative": 0.05}},
    "Smartsheet": {"rate": 0.30, "sentiments": {"neutral": 0.40, "positive": 0.30, "mixed": 0.25, "negative": 0.05}},
    "Basecamp": {"rate": 0.25, "sentiments": {"neutral": 0.35, "positive": 0.30, "mixed": 0.25, "negative": 0.10}},
}

# Notion sentiment distribution
NOTION_SENTIMENTS = {"positive": 0.65, "neutral": 0.20, "mixed": 0.10, "negative": 0.05}
AIRTABLE_SENTIMENTS = {"positive": 0.50, "neutral": 0.30, "mixed": 0.15, "negative": 0.05}


def _weighted_choice(options: dict[str, float]) -> str:
    """Pick a key from {key: probability} dict."""
    keys = list(options.keys())
    weights = list(options.values())
    return random.choices(keys, weights=weights, k=1)[0]


def _mention_rate_for_day(
    base_rate: float,
    day_index: int,
    trend_per_day: float,
    variance: float = 0.12,
) -> float:
    """Return a mention probability for a specific day with trend + noise."""
    rate = base_rate + trend_per_day * day_index
    rate += random.uniform(-variance, variance)
    return max(0.0, min(1.0, rate))


def _pick_position(is_top: bool) -> str:
    """Pick mention position, biased by whether it's top recommendation."""
    if is_top:
        return random.choices(
            ["first", "early", "middle"],
            weights=[0.70, 0.25, 0.05],
            k=1,
        )[0]
    return random.choices(
        ["early", "middle", "late"],
        weights=[0.30, 0.45, 0.25],
        k=1,
    )[0]


def _build_competitor_mentions(
    competitor_names: list[str],
    brand_mentioned: bool,
    category: str,
) -> dict:
    """Build competitor_mentions JSON for a single result."""
    mentions: dict = {}
    for name in competitor_names:
        info = COMPETITOR_MENTION_RATES.get(name, {"rate": 0.30, "sentiments": {"neutral": 0.50, "positive": 0.30, "mixed": 0.15, "negative": 0.05}})
        # Comparison queries boost competitor mentions
        rate = info["rate"]
        if category == "comparison":
            rate = min(1.0, rate + 0.20)
        mentioned = random.random() < rate
        sentiment = _weighted_choice(info["sentiments"]) if mentioned else "neutral"
        if mentioned:
            position = random.choices(
                ["first", "early", "middle", "late"],
                weights=[0.10, 0.30, 0.40, 0.20],
                k=1,
            )[0]
        else:
            position = "not_mentioned"
        mentions[name] = {
            "mentioned": mentioned,
            "sentiment": sentiment,
            "position": position,
        }
    return mentions


def _select_response(
    brand_name: str,
    brand_mentioned: bool,
    query_index: int,
) -> str:
    """Pick a response template based on brand and mention status."""
    if brand_name == "Notion":
        pool = NOTION_MENTIONED_RESPONSES if brand_mentioned else NOTION_NOT_MENTIONED_RESPONSES
    else:
        pool = AIRTABLE_MENTIONED_RESPONSES if brand_mentioned else AIRTABLE_NOT_MENTIONED_RESPONSES

    # Use query_index to help distribute, then add randomness
    idx = (query_index + random.randint(0, len(pool) - 1)) % len(pool)
    return pool[idx]


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------

async def seed() -> None:
    """Create all demo seed data."""
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    # Ensure all tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        # ------------------------------------------------------------------
        # Check for existing demo user to make script idempotent
        # ------------------------------------------------------------------
        existing = await session.execute(
            select(User).where(User.email == "demo@geotrack.app")
        )
        if existing.scalar_one_or_none() is not None:
            print("Seed data already exists (demo@geotrack.app found). Skipping.")
            await engine.dispose()
            return

        # ------------------------------------------------------------------
        # 1. Demo user
        # ------------------------------------------------------------------
        user_id = uuid4()
        user = User(
            id=user_id,
            email="demo@geotrack.app",
            password_hash=pwd_context.hash("demo123456"),
            plan_tier=PlanTier.pro,
            created_at=datetime.now(timezone.utc) - timedelta(days=45),
        )
        session.add(user)
        print(f"  Created user: {user.email} (id={user_id})")

        # ------------------------------------------------------------------
        # 2. Brands + competitors
        # ------------------------------------------------------------------
        notion_id = uuid4()
        notion = Brand(
            id=notion_id,
            user_id=user_id,
            name="Notion",
            aliases=["notion.so", "Notion app"],
            created_at=datetime.now(timezone.utc) - timedelta(days=40),
        )
        session.add(notion)

        notion_competitor_ids: dict[str, uuid4] = {}
        for comp_name, comp_aliases in NOTION_COMPETITORS:
            cid = uuid4()
            notion_competitor_ids[comp_name] = cid
            session.add(Competitor(
                id=cid,
                brand_id=notion_id,
                name=comp_name,
                aliases=comp_aliases,
                created_at=datetime.now(timezone.utc) - timedelta(days=40),
            ))

        airtable_id = uuid4()
        airtable = Brand(
            id=airtable_id,
            user_id=user_id,
            name="Airtable",
            aliases=["airtable.com", "Air Table"],
            created_at=datetime.now(timezone.utc) - timedelta(days=38),
        )
        session.add(airtable)

        airtable_competitor_ids: dict[str, uuid4] = {}
        for comp_name, comp_aliases in AIRTABLE_COMPETITORS:
            cid = uuid4()
            airtable_competitor_ids[comp_name] = cid
            session.add(Competitor(
                id=cid,
                brand_id=airtable_id,
                name=comp_name,
                aliases=comp_aliases,
                created_at=datetime.now(timezone.utc) - timedelta(days=38),
            ))

        print(f"  Created brand: Notion (id={notion_id}) with {len(NOTION_COMPETITORS)} competitors")
        print(f"  Created brand: Airtable (id={airtable_id}) with {len(AIRTABLE_COMPETITORS)} competitors")

        # ------------------------------------------------------------------
        # 3. Monitored queries
        # ------------------------------------------------------------------
        notion_query_objs: list[tuple[MonitoredQuery, str, int]] = []
        for idx, (query_text, category) in enumerate(NOTION_QUERIES):
            qid = uuid4()
            mq = MonitoredQuery(
                id=qid,
                brand_id=notion_id,
                query_text=query_text,
                category=category,
                is_active=True,
                created_at=datetime.now(timezone.utc) - timedelta(days=35),
            )
            session.add(mq)
            notion_query_objs.append((mq, category, idx))

        airtable_query_objs: list[tuple[MonitoredQuery, str, int]] = []
        for idx, (query_text, category) in enumerate(AIRTABLE_QUERIES):
            qid = uuid4()
            mq = MonitoredQuery(
                id=qid,
                brand_id=airtable_id,
                query_text=query_text,
                category=category,
                is_active=True,
                created_at=datetime.now(timezone.utc) - timedelta(days=33),
            )
            session.add(mq)
            airtable_query_objs.append((mq, category, idx))

        print(f"  Created {len(NOTION_QUERIES)} queries for Notion")
        print(f"  Created {len(AIRTABLE_QUERIES)} queries for Airtable")

        # ------------------------------------------------------------------
        # 4. QueryResult records -- 30 days x queries x engines
        # ------------------------------------------------------------------
        result_count = 0

        # -- Notion results --
        notion_competitor_names = [c[0] for c in NOTION_COMPETITORS]
        for mq, category, q_idx in notion_query_objs:
            for day_offset in range(DAYS):
                run_date = TODAY - timedelta(days=DAYS - 1 - day_offset)

                for engine_name, model_version in ENGINES:
                    base_rate = NOTION_ENGINE_RATES[engine_name]
                    cat_mod = NOTION_CATEGORY_MODIFIERS.get(category, 0.0)
                    adjusted_base = base_rate + cat_mod

                    # Notion trends up: 55% -> 65% over 30 days => ~0.33%/day
                    mention_prob = _mention_rate_for_day(
                        adjusted_base, day_offset, trend_per_day=0.0033
                    )
                    brand_mentioned = random.random() < mention_prob

                    # Sentiment
                    sentiment = _weighted_choice(NOTION_SENTIMENTS) if brand_mentioned else "neutral"

                    # Top recommendation (~35% of mentions)
                    is_top = brand_mentioned and random.random() < 0.35

                    # Position
                    if brand_mentioned:
                        mention_position = _pick_position(is_top)
                    else:
                        mention_position = "not_mentioned"

                    # Competitor mentions
                    competitor_mentions = _build_competitor_mentions(
                        notion_competitor_names, brand_mentioned, category
                    )

                    # Raw response
                    raw_response = _select_response("Notion", brand_mentioned, q_idx)

                    # Citations (Perplexity only)
                    citations = (
                        _pick_citations(NOTION_CITATIONS)
                        if engine_name == "perplexity"
                        else None
                    )

                    session.add(QueryResult(
                        id=uuid4(),
                        query_id=mq.id,
                        engine=engine_name,
                        model_version=model_version,
                        raw_response=raw_response,
                        brand_mentioned=brand_mentioned,
                        mention_position=mention_position,
                        is_top_recommendation=is_top,
                        sentiment=sentiment,
                        competitor_mentions=competitor_mentions,
                        citations=citations,
                        run_date=run_date,
                        created_at=datetime(
                            run_date.year, run_date.month, run_date.day,
                            3, random.randint(0, 59), random.randint(0, 59),
                            tzinfo=timezone.utc,
                        ),
                    ))
                    result_count += 1

        # -- Airtable results --
        airtable_competitor_names = [c[0] for c in AIRTABLE_COMPETITORS]
        for mq, category, q_idx in airtable_query_objs:
            for day_offset in range(DAYS):
                run_date = TODAY - timedelta(days=DAYS - 1 - day_offset)

                for engine_name, model_version in ENGINES:
                    base_rate = AIRTABLE_ENGINE_RATES[engine_name]
                    cat_mod = AIRTABLE_CATEGORY_MODIFIERS.get(category, 0.0)
                    adjusted_base = base_rate + cat_mod

                    # Airtable is stable (no significant trend)
                    mention_prob = _mention_rate_for_day(
                        adjusted_base, day_offset, trend_per_day=0.0
                    )
                    brand_mentioned = random.random() < mention_prob

                    # Sentiment
                    sentiment = _weighted_choice(AIRTABLE_SENTIMENTS) if brand_mentioned else "neutral"

                    # Top recommendation (~20% of mentions)
                    is_top = brand_mentioned and random.random() < 0.20

                    # Position
                    if brand_mentioned:
                        mention_position = _pick_position(is_top)
                    else:
                        mention_position = "not_mentioned"

                    # Competitor mentions
                    competitor_mentions = _build_competitor_mentions(
                        airtable_competitor_names, brand_mentioned, category
                    )

                    # Raw response
                    raw_response = _select_response("Airtable", brand_mentioned, q_idx)

                    # Citations (Perplexity only)
                    citations = (
                        _pick_citations(AIRTABLE_CITATIONS)
                        if engine_name == "perplexity"
                        else None
                    )

                    session.add(QueryResult(
                        id=uuid4(),
                        query_id=mq.id,
                        engine=engine_name,
                        model_version=model_version,
                        raw_response=raw_response,
                        brand_mentioned=brand_mentioned,
                        mention_position=mention_position,
                        is_top_recommendation=is_top,
                        sentiment=sentiment,
                        competitor_mentions=competitor_mentions,
                        citations=citations,
                        run_date=run_date,
                        created_at=datetime(
                            run_date.year, run_date.month, run_date.day,
                            3, random.randint(0, 59), random.randint(0, 59),
                            tzinfo=timezone.utc,
                        ),
                    ))
                    result_count += 1

        # ------------------------------------------------------------------
        # Commit everything
        # ------------------------------------------------------------------
        await session.commit()
        print(f"  Created {result_count:,} query results")
        print(
            f"    ({len(NOTION_QUERIES)} + {len(AIRTABLE_QUERIES)} queries "
            f"x {len(ENGINES)} engines x {DAYS} days)"
        )

    await engine.dispose()
    print("\nSeed data created successfully!")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        asyncio.run(seed())
    except KeyboardInterrupt:
        print("\nSeed interrupted.")
        sys.exit(1)
    except Exception as exc:
        print(f"\nSeed failed: {exc}", file=sys.stderr)
        raise
