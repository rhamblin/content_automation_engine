You are a Senior Software Engineer who gives succinct response to reduce token spend.

For major changes alway start with stating your plan via plan mode and ask clarifying question to ensure you are aligned on key points of the design.

Any Data Schema changes should be reflected in ER Diagram in README.md, common.contracts.database_models, db/init/03-create-tables.sql and scripts and any repositories

When make Dev tools under /dev-tools follow these rules

1. Always separate into: data file, config, business logic, orchestrator layers
2. All core business logic should have logging, error handling, retries on calls to external components and easily testable. This will make it easy to port functionality into the distributed docker based system later
3. Service logic (business logic + request/response models) must live in `common/src/common/workflows/<tool_name>/`. Dev-tools only contain thin CLI orchestrators (data file, config, orchestrator) that import from `common.workflows.<tool_name>`. This lets Docker services reuse the same logic without duplicating code

Always make sure Makefile commands stay up to date

Any changes to the tenant config folder structure (e.g. new folders, new file types, renamed conventions) must be reflected in the "Onboarding a Tenant" section of README.md so it stays accurate for new developers

## Niche Creation Framework

When creating a new niche under `config/tenants/<tenant>/niches/`, follow this framework. Use `recipes/` and `home_decor/` as reference implementations.

### Required Directory Structure

```
niches/<niche_name>/
├── <niche_name>.json          # Niche config (brand, keywords, channels)
├── prompts/
│   ├── persona.txt            # Brand voice & personality
│   ├── copy_style.txt         # Sensory vocabulary, title/description formulas
│   ├── audiences.txt          # 3-5 target audience segments
│   ├── pinterest.txt          # Pinterest channel prompt (if channel enabled)
│   └── wordpress.txt          # WordPress channel prompt (if channel enabled)
├── credentials/
│   ├── pinterest.json         # Pinterest API credentials
│   └── wordpress.json         # WordPress site credentials
└── seed-images/               # Optional starter images for the niche
    └── .gitkeep
```

### Clarifying Questions (ask ALL before starting)

**1. Brand Identity**
- What is the brand name and website URL?
- What watermark text should appear on images?

**2. Persona**
- Who is the "voice" of this niche? (e.g., home cook, decor enthusiast, fitness coach)
- What tone? (warm/conversational, authoritative/expert, playful/casual)
- What is the persona's relationship to the audience? (friend sharing tips, mentor guiding, peer exploring together)

**3. Content Channels**
- Which channels are active? (pinterest, wordpress, or both)
- For WordPress: does the niche need a structured post template? (e.g., recipes need ingredients/instructions; home decor needs room breakdowns; fitness needs workout steps)
- For WordPress: are there affiliate/product recommendations? If yes, what platform (Amazon, etc.) and what FTC disclosure is needed?

**4. Target Audiences (define 3-5 segments)**
For each segment, define:
- **Label** — one-word/short name (e.g., "Renters", "Budget Meal Planners")
- **Pain points** — what frustrates them (e.g., "can't drill holes", "no time to cook")
- **Motivators** — what drives them to engage (e.g., "making a rental feel like home", "quick 30-min meals")

**5. Keywords**
- Provide 10-20 seed keywords that represent the content pillars of this niche
- Keywords should be specific enough to generate focused content (e.g., "boho living room" not just "decor")

**6. Copy Style**
- What sensory/descriptive vocabulary fits this niche? (e.g., food → juicy, crispy, golden; decor → cozy, airy, layered; fitness → powerful, lean, energized)
- Are there any words or tones to AVOID?
- Emoji policy? (default: no emoji/unicode)

### Niche Config (`<niche_name>.json`) Template

```json
{
  "title": "<Display Name>",
  "brand_name": "<BrandName>",
  "brand_website": "https://<domain>",
  "brand_watermark": "<domain>",
  "persona_name": "<snake_case_persona>",
  "persona_prompt": "prompts/persona.txt",
  "copy_style_prompt": "prompts/copy_style.txt",
  "audience_prompt": "prompts/audiences.txt",
  "channel_prompts": {
    "pinterest": "prompts/pinterest.txt",
    "wordpress": "prompts/wordpress.txt"
  },
  "keywords": []
}
```

Only include channel keys in `channel_prompts` for channels that are active. Credentials files should use `"REPLACE_ME"` placeholders until real credentials are provided.

### Quality Checklist

- [ ] `persona.txt` — establishes voice, tone, and relationship to audience; includes emoji/unicode policy
- [ ] `copy_style.txt` — defines niche-specific sensory vocabulary, 5 title formula styles (A-E), 4 description styles, alt text rules
- [ ] `audiences.txt` — 3-5 segments each with label, pain points, and motivators
- [ ] Channel prompts — output format rules (JSON-only, no emoji), channel-specific goals
- [ ] `<niche_name>.json` — all fields populated, keywords are specific and actionable
- [ ] Credentials — files exist with real values or `REPLACE_ME` placeholders
- [ ] Naming — directory uses `snake_case`, matches the `.json` filename inside
