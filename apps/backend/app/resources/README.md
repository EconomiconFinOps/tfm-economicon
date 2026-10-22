# Public RDS trust bundle

`rds-eu-south-2.pem` is the public CA bundle downloaded on 2026-10-22 from
https://truststore.pki.rds.amazonaws.com/eu-south-2/eu-south-2-bundle.pem.
SHA256: `6e4db6870d865a83140270728f62fbdb73202a3a017dc500ae2605e3d17344c0`.
It contains three self-issued Amazon RDS Spain roots, no private keys or
project credentials. This is trust material, not proof of database access.

In explicit ECS mode, `app.aws_runtime` verifies the packaged hash, sets
`PGSSLROOTCERT` and requires `sslmode=verify-full` for both PostgreSQL DSNs.
Local database modes retain their existing configuration. No download occurs
at runtime. Update both app copies, hash and tests together after reviewing
an official bundle rotation.

AWS references:
- https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.SSL.html
- https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL.Concepts.General.SSL.html
