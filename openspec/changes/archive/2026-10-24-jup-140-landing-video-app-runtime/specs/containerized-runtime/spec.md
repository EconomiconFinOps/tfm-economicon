## ADDED Requirements

### Requirement: Private writable processor temporary workspace

The general Compose runtime SHALL mount the processor temporary workspace with uid10001, gid10001 and mode0700, matching its existing unprivileged image user, while preserving read-only root and no-new-privileges. The mount SHALL permit local tokenizer loading and startup without requiring a separate tmpfs override or changing processor code, image user or Dockerfile.

#### Scenario: General startup with the existing processor image
- **WHEN** the operator starts the isolated general stack with the required local configuration
- **THEN** the processor runs as its existing unprivileged user and /tmp reports uid10001, gid10001 and mode0700
- **AND** the workspace is writable by that user, tempfile.gettempdir selects /tmp and the processor reports healthy
- **AND** the landing and existing services operate without a processor tmpfs overlay, privileged user or expanded access
