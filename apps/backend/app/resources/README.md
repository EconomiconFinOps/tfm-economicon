# Public RDS trust bundle

`rds-eu-west-1.pem` is the public CA bundle downloaded on 2026-10-22 from
https://truststore.pki.rds.amazonaws.com/eu-west-1/eu-west-1-bundle.pem.
SHA256: `a11cf9a1d0aadd7db86f92cbaa496466daeb501bf1c5e429d8ce8914a01c15d6`.
It contains three self-issued Amazon RDS Ireland roots, no private keys or
project credentials. This is trust material, not proof of database access.

In explicit ECS mode, `app.aws_runtime` verifies the packaged hash, sets
`PGSSLROOTCERT` and requires `sslmode=verify-full` for both PostgreSQL DSNs.
Local database modes retain their existing configuration. No download occurs
at runtime. Update both app copies, hash and tests together after reviewing
an official bundle rotation.

AWS references:
- https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.SSL.html
- https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL.Concepts.General.SSL.html
