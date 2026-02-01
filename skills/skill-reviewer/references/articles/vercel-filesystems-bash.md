Title: How to build agents with filesystems and bash - Vercel

URL Source: https://vercel.com/blog/how-to-build-agents-with-filesystems-and-bash

Markdown Content:
How to build agents with filesystems and bash - Vercel
===============

[![Image 1: VercelLogotype](https://vercel.com/vc-ap-vercel-marketing/_next/static/media/vercel-logotype-light.64164313.svg?dpl=dpl_5ysmsV7mJv3Ax5akWnAYR2isgxsQ)![Image 2: VercelLogotype](https://vercel.com/vc-ap-vercel-marketing/_next/static/media/vercel-logotype-dark.49dd0a95.svg?dpl=dpl_5ysmsV7mJv3Ax5akWnAYR2isgxsQ)](https://vercel.com/home)

*   Products

    *   ##### [AI Cloud](https://vercel.com/ai)

        *   [v0 Build applications with AI](https://v0.app/)
        *   [AI SDK The AI Toolkit for TypeScript](https://sdk.vercel.ai/)
        *   [AI Gateway One endpoint, all your models](https://vercel.com/ai-gateway)
        *   [Vercel Agent An agent that knows your stack](https://vercel.com/agent)
        *   [Sandbox AI workflows in live environments](https://vercel.com/sandbox)

    *   ##### Core Platform

        *   [CI/CD Helping teams ship 6× faster](https://vercel.com/products/previews)
        *   [Content Delivery Fast, scalable, and reliable](https://vercel.com/products/rendering)
        *   [Fluid Compute Servers, in serverless form](https://vercel.com/fluid)
        *   [Observability Trace every step](https://vercel.com/products/observability)

    *   ##### [Security](https://vercel.com/security)

        *   [Bot Management Scalable bot protection](https://vercel.com/security/bot-management)
        *   [BotID Invisible CAPTCHA](https://vercel.com/botid)
        *   [Platform Security DDoS Protection, Firewall](https://vercel.com/security)
        *   [Web Application Firewall Granular, custom protection](https://vercel.com/security/web-application-firewall)

*   Resources

    *   ##### Company

        *   [Customers Trusted by the best teams](https://vercel.com/customers)
        *   [Blog The latest posts and changes](https://vercel.com/blog)
        *   [Changelog See what shipped](https://vercel.com/changelog)
        *   [Press Read the latest news](https://vercel.com/press)
        *   [Events Join us at an event](https://vercel.com/events)

    *   ##### Learn

        *   [Docs Vercel documentation](https://vercel.com/docs)
        *   [Academy Linear courses to level up](https://vercel.com/academy)
        *   [Knowledge Base Find help quickly](https://vercel.com/kb)
        *   [Community Join the conversation](https://community.vercel.com/)

    *   ##### Open Source

        *   [Next.js The native Next.js platform](https://vercel.com/frameworks/nextjs)
        *   [Nuxt The progressive web framework](https://nuxt.com/)
        *   [Svelte The web’s efficient UI framework](https://svelte.dev/)
        *   [Turborepo Speed with Enterprise scale](https://vercel.com/solutions/turborepo)

*   Solutions

    *   ##### Use Cases

        *   [AI Apps Deploy at the speed of AI](https://vercel.com/solutions/ai-apps)
        *   [Composable Commerce Power storefronts that convert](https://vercel.com/solutions/composable-commerce)
        *   [Marketing Sites Launch campaigns fast](https://vercel.com/solutions/marketing-sites)
        *   [Multi-tenant Platforms Scale apps with one codebase](https://vercel.com/solutions/multi-tenant-saas)
        *   [Web Apps Ship features, not infrastructure](https://vercel.com/solutions/web-apps)

    *   ##### Tools

        *   [Marketplace Extend and automate workflows](https://vercel.com/marketplace)
        *   [Templates Jumpstart app development](https://vercel.com/templates)
        *   [Partner Finder Get help from solution partners](https://vercel.com/partners/solution-partners)

    *   ##### Users

        *   [Platform Engineers Automate away repetition](https://vercel.com/solutions/platform-engineering)
        *   [Design Engineers Deploy for every idea](https://vercel.com/solutions/design-engineering)

*   [Enterprise](https://vercel.com/enterprise)
*   [Pricing](https://vercel.com/pricing)

[Blog](https://vercel.com/blog)

How to build agents with filesystems and bash
=============================================

[![Image 3](https://assets.vercel.com/image/upload/contentful/image/e5382hct74si/4r50teDxMgOdYgpMyyX9uT/8733ddb27e28c92caf43210713e3f4c6/T0CAQ00TU-U09SA36V1ST-5eb8fa5a5948-128.jpg) Ashka Stephen Software Engineer](https://twitter.com/ashka-stephen)

3 min read

Copy URL

Copied to clipboard!

Jan 9, 2026

The best agent architecture is already sitting in your terminal

Many of us have built complex tooling to feed our agents the right information. It's brittle because we're guessing what the model needs instead of letting it find what it needs. We've found a simpler approach. We replaced most of the custom tooling in our internal agents with a filesystem tool and a bash tool. Our sales call summarization agent went from ~$1.00 to ~$0.25 per call on Claude Opus 4.5, and the output quality improved. [We used the same approach for d0](https://vercel.com/blog/we-removed-80-percent-of-our-agents-tools), our text-to-SQL agent.

The idea behind this is that LLMs have been trained on massive amounts of code. They've spent countless hours navigating directories, grepping through files, and managing state across complex codebases. If agents excel at filesystem operations for code, they'll excel at filesystem operations for anything. Agents already understand filesystems.

Customer support tickets, sales call transcripts, CRM data, conversation history. Structure it as files, give the agent bash, and the model brings the same capabilities it uses for code navigation.

[Link to heading](https://vercel.com/blog/how-to-build-agents-with-filesystems-and-bash#how-agents-read-filesystems)How agents read filesystems
-----------------------------------------------------------------------------------------------------------------------------------------------

The agent runs in a sandbox with your data structured as files. When it needs context, it explores the filesystem using Unix commands, pulls in what's relevant, and sends that to the LLM.

`1Agent receives task2    ↓3Explores filesystem (ls, find)4    ↓5Searches for relevant content (grep, cat)6    ↓7Sends context + request to LLM8    ↓9Returns structured output`

The agent and its tool execution run on separate compute. You trust the agent's reasoning, but the sandbox isolates what it can actually do.

[Link to heading](https://vercel.com/blog/how-to-build-agents-with-filesystems-and-bash#why-filesystems-work-for-context-management)Why filesystems work for context management
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

The typical approach to agent context is either stuffing everything into the prompt or using vector search. Prompt stuffing hits token limits. Vector search works for semantic similarity but returns imprecise results when you need a specific value from structured data.

Filesystems offer a different tradeoff.

**Structure matches your domain.** Customer records, ticket history, CRM data. These have natural hierarchies that map directly to directories. You're not flattening relationships into embeddings.

**Retrieval is precise.**`grep -r "pricing objection" transcripts/` returns exact matches. When you need one specific value, you get that value.

**Context stays minimal.** The agent loads files on demand. A large transcript doesn't go into the prompt upfront. The agent reads the metadata, greps for relevant sections, then pulls only what it needs.

[Link to heading](https://vercel.com/blog/how-to-build-agents-with-filesystems-and-bash#mapping-your-domain-to-files)Mapping your domain to files
-------------------------------------------------------------------------------------------------------------------------------------------------

Let's look at some concrete examples of how different domains map to filesystem structures.

**Example 1: Customer support system**

Instead of throwing raw JSON into your agent, structure it:

`1/customers/2  /cust_12345/3    profile.json          # High-level info4    tickets/5      ticket_001.md       # Each ticket6      ticket_002.md7    conversations/8      2024-01-15.txt      # Daily conversation logs9    preferences.json`

When a customer asks "What was the resolution to my issue?", the agent can `ls` the tickets directory, `grep` for "resolved", and read only the relevant file.

**Example 2: Document analysis system**

`1/documents/2  /uploaded/3    contract_abc123.pdf4    invoice_def456.pdf5  /extracted/6    contract_abc123.txt7    invoice_def456.txt8  /analysis/9    contract_abc123/10      summary.md11      key_terms.json12      risk_assessment.md13  14/templates/15  contract_analysis_prompt.md16  invoice_validation_rules.md`

Raw inputs in one place, processed outputs in structured directories. The agent can reference previous analysis without reprocessing.

[Link to heading](https://vercel.com/blog/how-to-build-agents-with-filesystems-and-bash#case-study:-sales-call-summary-agent)Case study: Sales call summary agent
-----------------------------------------------------------------------------------------------------------------------------------------------------------------

We built a [sales call summary template](https://vercel.com/templates/ai/call-summary-agent) using this architecture. The agent analyzes sales call transcripts and generates structured summaries with objections, action items, and insights.

The agent sees this file structure:

```
1gong-calls/2  demo-call-001-companyname-product-demo.md     # Current call transcript3  metadata.json                                 # Call metadata4  previous-calls/5    demo-call-000-discovery-call.md             # Prior discovery call6    demo-call-intro-initial-call.md             # Initial intro call7
8salesforce/9  account.md                                    # CRM account record10  opportunity.md                                # Deal/opportunity details11  contacts.md                                   # Contact profiles12
13slack/14  slack-channel.md                              # Slack history15
16research/17  company-research.md                           # Company background18  competitive-intel.md                          # Competitor analysis19
20playbooks/21  sales-playbook.md                             # Internal sales playbook22
```

The agent explores this like a codebase:

```
1# Explore what's available2$ ls sales-calls/3customer-call-123456-q4.md4metadata.json5
6# Read the metadata7$ cat sales-calls/metadata.json8
9# Look for objections10$ grep -i "concern\|worried\|issue\|problem" sales-calls/*.md
```

The intuition is that the agent treats the transcript like a codebase. It searches for patterns, reads sections, and builds context just like it would debug code. No custom retrieval logic. The agent decides what context it needs using tools it already knows how to use. It handles edge cases we never anticipated because it's working with the raw information, not parameters we defined.

We'll have another post diving deeper into the sales call summary agent.

[Link to heading](https://vercel.com/blog/how-to-build-agents-with-filesystems-and-bash#why-you-should-use-bash-and-filesystems)Why you should use bash and filesystems
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------

**Native model capabilities.** grep, cat, find, awk. These aren't new skills we're teaching. LLMs have seen these tools billions of times during training. They're native operations, not bolted on behaviors.

**Future-proof architecture.** As models get better at coding, your agent gets better. Every improvement in code understanding translates directly. You're leveraging the training distribution instead of fighting against it.

**Debuggability.** When the agent fails, you see exactly what files it read and what commands it ran. The execution path is visible. No black box.

**Security through isolation.** The sandbox lets the agent explore files without access to production systems. You trust the reasoning, not the execution environment.

**Less code to maintain.** Instead of building retrieval pipelines for each data type, you write files to a directory structure. The agent handles the rest.

[Link to heading](https://vercel.com/blog/how-to-build-agents-with-filesystems-and-bash#get-started)Get started
---------------------------------------------------------------------------------------------------------------

Every agent needs filesystem and bash. If you're building an agent, resist the urge to create custom tools. Instead, ask: can I represent this as files?

We recently open-sourced [bash-tool](https://vercel.com/changelog/introducing-bash-tool-for-filesystem-based-context-retrieval), a dedicated tool that powers this pattern.

1.   [**AI SDK**](https://ai-sdk.dev/docs/introduction) for tool execution and model calls

2.   [**bash-tool**](https://www.npmjs.com/package/bash-tool) for sandboxed filesystem access

3.   [**Sales Call Summary template**](https://vercel.com/templates/ai/call-summary-agent) to see the full pattern and to get started with one-click

The future of agents might be surprisingly simple. Maybe the best architecture is almost no architecture at all. Just filesystems and bash.

[**Get started with filesystem agents** The Sales Call Summary template shows the filesystem and bash pattern in production. Deploy it on Vercel and watch the agent explore files in real time. Deploy the template](https://vercel.com/templates/ai/call-summary-agent)

**Ready to deploy?**Start building with a free account. Speak to an expert for your _Pro_ or Enterprise needs.

[Start Deploying](https://vercel.com/new)[Talk to an Expert](https://vercel.com/contact/sales)

**Explore Vercel Enterprise** with an interactive product tour, trial, or a personalized demo.

[Explore Enterprise](https://vercel.com/try-enterprise)

Products
--------

*   [AI](https://vercel.com/ai)
*   [Enterprise](https://vercel.com/enterprise)
*   [Fluid Compute](https://vercel.com/fluid)
*   [Next.js](https://vercel.com/solutions/nextjs)
*   [Observability](https://vercel.com/products/observability)
*   [Previews](https://vercel.com/products/previews)
*   [Rendering](https://vercel.com/products/rendering)
*   [Security](https://vercel.com/security)
*   [Turbo](https://vercel.com/solutions/turborepo)
*   [Domains](https://vercel.com/domains)
*   [Sandbox](https://vercel.com/sandbox)
*   [v0](https://v0.app/)

Resources
---------

*   [Community](https://community.vercel.com/)
*   [Docs](https://vercel.com/docs)
*   [Knowledge Base](https://vercel.com/kb)
*   [Academy](https://vercel.com/academy)
*   [Help](https://vercel.com/help)
*   [Integrations](https://vercel.com/integrations)
*   [Platforms](https://vercel.com/platforms)
*   [Pricing](https://vercel.com/pricing)
*   [Resources](https://vercel.com/resources)
*   [Solution Partners](https://vercel.com/partners/solution-partners)
*   [Startups](https://vercel.com/startups)
*   [Templates](https://vercel.com/templates)
*   SDKs by Vercel
    *   [AI SDK](https://sdk.vercel.ai/)
    *   [Workflow DevKit](https://useworkflow.dev/)
    *   [Flags SDK](https://flags-sdk.dev/)
    *   [Chat SDK](https://chat-sdk.dev/)
    *   [Streamdown AI](https://streamdown.ai/)

Company
-------

*   [About](https://vercel.com/about)
*   [Blog](https://vercel.com/blog)
*   [Careers](https://vercel.com/careers)
*   [Changelog](https://vercel.com/changelog)
*   [Contact Us](https://vercel.com/contact)
*   [Customers](https://vercel.com/customers)
*   [Events](https://vercel.com/events)
*   [Partners](https://vercel.com/partners)
*   [Shipped](https://vercel.com/shipped)
*   [Privacy Policy](https://vercel.com/legal/privacy-policy)
*   Legal

Social
------

*   [GitHub](https://github.com/vercel)
*   [LinkedIn](https://linkedin.com/company/vercel)
*   [Twitter](https://x.com/vercel)
*   [YouTube](https://youtube.com/@VercelHQ)

[](https://vercel.com/home)

[Loading status…](https://vercel-status.com/)Select a display theme:system light dark 

Products

[v0 Build applications with AI](https://v0.app/)

[AI SDK The AI Toolkit for TypeScript](https://sdk.vercel.ai/)

[AI Gateway One endpoint, all your models](https://vercel.com/ai-gateway)

[Vercel Agent An agent that knows your stack](https://vercel.com/agent)

[Sandbox AI workflows in live environments](https://vercel.com/sandbox)

[CI/CD Helping teams ship 6× faster](https://vercel.com/products/previews)

[Content Delivery Fast, scalable, and reliable](https://vercel.com/products/rendering)

[Fluid Compute Servers, in serverless form](https://vercel.com/fluid)

[Observability Trace every step](https://vercel.com/products/observability)

[Bot Management Scalable bot protection](https://vercel.com/security/bot-management)

[BotID Invisible CAPTCHA](https://vercel.com/botid)

[Platform Security DDoS Protection, Firewall](https://vercel.com/security)

[Web Application Firewall Granular, custom protection](https://vercel.com/security/web-application-firewall)

Resources

[Customers Trusted by the best teams](https://vercel.com/customers)

[Blog The latest posts and changes](https://vercel.com/blog)

[Changelog See what shipped](https://vercel.com/changelog)

[Press Read the latest news](https://vercel.com/press)

[Events Join us at an event](https://vercel.com/events)

[Docs Vercel documentation](https://vercel.com/docs)

[Academy Linear courses to level up](https://vercel.com/academy)

[Knowledge Base Find help quickly](https://vercel.com/kb)

[Community Join the conversation](https://community.vercel.com/)

[Next.js The native Next.js platform](https://vercel.com/frameworks/nextjs)

[Nuxt The progressive web framework](https://nuxt.com/)

[Svelte The web’s efficient UI framework](https://svelte.dev/)

[Turborepo Speed with Enterprise scale](https://vercel.com/solutions/turborepo)

Solutions

[AI Apps Deploy at the speed of AI](https://vercel.com/solutions/ai-apps)

[Composable Commerce Power storefronts that convert](https://vercel.com/solutions/composable-commerce)

[Marketing Sites Launch campaigns fast](https://vercel.com/solutions/marketing-sites)

[Multi-tenant Platforms Scale apps with one codebase](https://vercel.com/solutions/multi-tenant-saas)

[Web Apps Ship features, not infrastructure](https://vercel.com/solutions/web-apps)

[Marketplace Extend and automate workflows](https://vercel.com/marketplace)

[Templates Jumpstart app development](https://vercel.com/templates)

[Partner Finder Get help from solution partners](https://vercel.com/partners/solution-partners)

[Platform Engineers Automate away repetition](https://vercel.com/solutions/platform-engineering)

[Design Engineers Deploy for every idea](https://vercel.com/solutions/design-engineering)
