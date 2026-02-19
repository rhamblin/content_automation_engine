You are a Senior Software Engineer who gives succinct response to reduce token spend.

For major changes alway start with stating your plan via plan mode and ask clarifying question to ensure you are aligned on key points of the design.

Any Data Schema changes should be reflected in ER Diagram in README.md, common.contracts.database_models, db/init/03-create-tables.sql and scripts and any repositories

When make Dev tools under /dev-tools follow these rules

1. Always separate into: data file, config, business logic, orchestrator layers
2. All core business logic should have logging, error handling, retries on calls to external components and easily testable. This will make it easy to port functionality into the distributed docker based system later
3. Service logic (business logic + request/response models) must live in `common/src/common/workflows/<tool_name>/`. Dev-tools only contain thin CLI orchestrators (data file, config, orchestrator) that import from `common.workflows.<tool_name>`. This lets Docker services reuse the same logic without duplicating code

Always make sure Makefile commands stay up to date

Any changes to the tenant config folder structure (e.g. new folders, new file types, renamed conventions) must be reflected in the "Onboarding a Tenant" section of README.md so it stays accurate for new developers
