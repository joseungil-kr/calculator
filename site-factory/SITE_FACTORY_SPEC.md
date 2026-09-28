# Local Site Factory Specification

## 1. Goal

Build many independent local expert sites by combining a region, an industry blueprint, a site identity, and a content memory system.

The system must not mass-publish region-name substitutions. Each site must behave like an independent local editorial property with its own:
- region and industry scope
- persona/tone
- editorial mission
- local entities
- content pillars
- topic memory
- structure memory
- fact verification sources
- internal-link architecture

## 2. Core roles

### Codex / Infrastructure Lead
- create site from standard template
- repository, branch and deployment setup
- content collections and route structure
- sitemap, robots, canonical, schema
- GitHub Actions
- search registration helpers
- high-risk refactors and structural fixes

### Worker Chat
- reads Sites + Industry Blueprints + Topic Registry + Page Plan
- selects the next approved/planned topic
- researches local facts when needed
- writes a unique draft
- records source URLs and verification time
- never invents delivery history, customer reviews, or operating experience

### Editorial Chat
- checks local specificity, answer quality, factual grounding
- checks global similarity against same-industry sites
- checks structure similarity
- PASS / REVISE / REJECT
- writes structure_type and similarity memory back to Topic Registry

### Publisher
- only publishes PASS/approved content
- Airtable Queue -> GitHub event -> GitHub Actions -> commit -> deployment
- deterministic and idempotent

### Webmaster Chat
- verifies deployed content
- checks HTTP status, sitemap, canonical, internal links, orphan pages, missing hubs
- LOW-risk issues go to Fix Queue
- rechecks repairs and records commit/result

### Repair Worker
- deterministic GitHub Actions/scripts
- receives structured Fix Queue commands
- only performs allow-listed repairs
- build/test before commit
- idempotent and path-restricted

## 3. Airtable control plane

### Sites
Single source of truth for each site:
- site_key
- domain
- region
- industry
- blueprint_key
- brand_name
- persona
- editorial_mission
- local_entities
- content_pillars
- forbidden_patterns
- tone
- answer_rules
- initial_page_target
- daily_count
- factory_status
- repo / branch / content_root
- repo_status / deploy_status / search_status / webmaster_status

### Industry Blueprints
Defines industry-level content DNA:
- expertise_axes
- content_pillars
- structure_pool
- fact_source_priority
- forbidden_patterns
- launch_mix_rule
- daily_rule

### Page Plan
Planning layer for launch pages and daily backlog:
- page_key
- site_key
- phase
- publish_order
- pillar
- entity
- search_intent
- structure_type
- title
- primary_question
- slug
- region_specificity_goal
- similarity_risk_goal
- source_requirement
- internal_link_hub
- status

### Topic Registry
Long-term content memory:
- primary_question
- intent
- pillar
- entity
- season
- title / slug
- structure_type
- source_urls / verified_at
- global_similarity
- similarity_notes
- status

### Draft Lab
Pre-publication quality gate:
- content_md
- meta_description
- image_prompt / image_alt
- structure_type
- source_urls / verified_at
- region_specificity
- answer_quality
- global_similarity
- structure_similarity
- review_status
- review_notes

### Queue
Approved content only.
Publisher consumes this table.

### Fix Queue
Structured repair jobs only:
- issue_type
- action
- source_file
- target_url
- anchor_text
- risk_level
- status
- commit_sha

## 4. Content rules

### Local identity
A local page must contain a reason to exist beyond replacing the city name.

Bad:
- "Ansan flower delivery is fast..."
- same headings and arguments as Suwon with city names swapped

Good:
- a local entity, event, relationship, space, season or practical question changes the editorial reasoning itself

### Structure memory
Examples:
- recipient_based
- route_based
- relationship_based_b2b
- space_based_event
- comparison
- checklist
- etiquette_guide
- care_guide
- seasonal_guide
- decision_tree
- timing_guide
- message_guide
- risk_based
- scenario_based
- faq_first
- myth_busting
- product_form_comparison

Workers must inspect recently used structures before drafting.
Do not repeatedly reuse the same structure across same-industry sites.

### AEO/GEO-oriented answer design
- answer the main question early
- connect concrete entities to the actual decision
- use clear subquestions and concise explanations
- only include FAQ when useful; do not force identical templates
- use citations/source memory for concrete local facts
- never fabricate experience signals

## 5. Launch strategy

Default launch target: 30 pages.

Flower blueprint mix:
- Core/hub: 6
- Local entities: 8
- Seasonal/event: 6
- Flower expertise: 5
- Purchase-intent/practical: 5

After launch:
- publish approximately one new page per day
- choose gaps from Sites + Topic Registry + Page Plan
- consider season and local events
- avoid recent same-industry structure repetition

## 6. Quality gates

A draft should only advance when:
- local specificity is strong
- direct answer quality is strong
- no fabricated experience
- local facts have source URLs + verified_at when required
- no duplicate slug/title/question
- global similarity target is respected
- structure similarity target is respected

Suggested editorial threshold:
- region_specificity >= 8/10 for entity/local pages
- answer_quality >= 8/10
- global_similarity <= 35/100
- structure_similarity <= 35/100

## 7. Publishing state machine

Page Plan:
planned -> drafting -> review -> approved -> queued -> published

Site:
planning -> plan_ready -> building -> content_ready -> deploying -> live

Draft:
pending -> pass | revise | reject

Fix:
pending -> dispatched -> resolved | failed

## 8. Safety and factual integrity

Never claim:
- fake years of local operation
- fake customer orders or delivery experience
- fake reviews
- unverified facility rules
- unverified event dates or opening hours
- guaranteed delivery/index/ranking outcomes

Local facts that may change should store:
- source_urls
- source_titles where available
- verified_at

## 9. Webmaster / self-healing

Automatically repair only allow-listed LOW-risk issues first:
- orphan page -> add approved internal link
- missing hub link
- deterministic broken internal link replacement
- deterministic sitemap inclusion
- missing alt when source data exists

Escalate structural/high-risk work:
- URL architecture
- bulk redirects
- schema architecture
- navigation redesign
- template refactor
- ambiguous duplicate content

## 10. Scaling

Do not create one Chat per site at large scale.
Use worker pools by industry and let each run load site-specific identity from Airtable.

Target architecture:
Site Registry + Industry Blueprint
-> Planner
-> Worker Pool
-> Editorial Gate
-> Queue
-> GitHub Publisher
-> Deployment
-> Webmaster
-> Fix Queue / Repair Worker

The data, not the chat thread, is the durable memory.
