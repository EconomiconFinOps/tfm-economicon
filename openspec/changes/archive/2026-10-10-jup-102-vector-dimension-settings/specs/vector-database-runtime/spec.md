## ADDED Requirements

### Requirement: Effective vector dimension configuration
For a new vector database, the processor SHALL create the vector column using
the same resolved dimension passed from Settings to PgVectorStore. Migrations
SHALL NOT independently read the process environment or another Settings instance.
Settings precedence SHALL remain explicit constructor values, process environment,
the file selected by ECONOMICON_ENV_FILE, then the default dimension of eight.

#### Scenario: Dimension provided exclusively by an environment file
- **WHEN** Settings resolves dimension 16 exclusively from ECONOMICON_ENV_FILE
- **THEN** initial migrations create vector(16), record 001 and 002, and startup succeeds without a duplicate export.

#### Scenario: Environment takes precedence over the selected file
- **WHEN** the file specifies dimension 16 and the process environment specifies dimension 12
- **THEN** Settings, migrations and startup all use dimension 12.

#### Scenario: Default and explicit Settings values
- **WHEN** no dimension is configured, or the caller supplies an explicit Settings dimension
- **THEN** migrations use eight or the explicit value respectively, matching the constructed store.

#### Scenario: Restart on an existing matching volume
- **WHEN** the configured dimension matches an already migrated, populated vector database
- **THEN** initialization succeeds repeatedly and preserves ledger entries, schema, vectors and tenant-scoped retrieval.

#### Scenario: Restart on an incompatible volume
- **WHEN** the configured dimension differs from an already migrated, populated vector database
- **THEN** startup raises the actionable StartupError without resizing the column or deleting or converting stored vectors.
