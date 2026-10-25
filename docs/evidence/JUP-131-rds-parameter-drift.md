# JUP-131 — PostgreSQL parameter drift during the first AWS rehearsal

Verified 2026-10-25 in the master's account `323188184300`, Ireland. Origin:
«Preparar despliegue en AWS», chat `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.

The first infrastructure apply reached a partial state after Cloud Map denied
private namespace creation. The namespace was subsequently created through the
authorized SSO session and imported into the same state. The new recovery plan
then correctly stopped: besides three missing Cloud Map services it proposed an
unrelated update to `aws_db_parameter_group.main.parameter.apply_method` from
`pending-reboot` to `immediate`. No recovery apply or application release ran.

AWS `DescribeDBParameters` on the actual `postgres16` group returned
`rds.force_ssl=1`, `ApplyType=dynamic`, `ApplyMethod=pending-reboot`, `Source=system`.
The two database instances reported `ParameterApplyStatus=in-sync`. The original
Terraform declaration omitted the apply method, selecting the provider's default
`immediate`. This change explicitly declares the persisted method. It preserves
the SSL value and avoids unrelated changes in the guarded release and teardown
plans; it does not classify the parameter as static or request a database reboot.

Local regression: the architecture test first failed on the new TLS/apply-method
assertion (13 other Terraform tests passed). After the explicit declaration,
`terraform -chdir=infra/aws-reference test -filter=tests/architecture.tftest.hcl`
passed all seven architecture scenarios. On Windows the filter uses a backslash.
Terraform formatting also passed. `ApiError`, the application sources and
`starlette==1.9.0` are unchanged.

The retired rehearsal used an explicitly recorded operational Terraform override
with the identical parameter block, because its source archive is pinned to
`0a36a663463a57227da676c40710f9614f73eba2`. Override SHA256:
`fe57d673f07ead07023076522578bb609a378dce4ac9d7cc8bfc0ab3e96de905`.
The expiry buildspec was independently reviewed and its readback verified;
account, source, configuration, scheduled time, IAM role, DLQ and retries remain
the same. This is an operational recovery, not a successful end-to-end pipeline
or authorization to merge this new patch. The existing PR165 exception does not
extend to this PR. Release and teardown plan allowlists remain unchanged.

Public local evidence is in `.work/master-rehearsal/recovery-1/plan-inspection.json`,
`rds-parameter-evidence.json` and `recovery-2/expiry-protected.json`; the parameter
receipt includes a fresh read at 15:21:36 UTC and attributes the original red
test output to the coordinator. Private plan/state/secret values are not
included. Current retirement status and next steps are maintained in
[`cloud-aws.md`](../continuidad/cloud-aws.md).

## Authoritative retirement inventory and integrated CI

Terraform removed every managed resource on 25 October at 15:35:52 UTC. The
retirement build still failed its inventory guard because the tagging API
returned 39 historical ARNs. Direct service reads subsequently confirmed all
39 retired, most recently at 15:47:50 UTC. The separately authorized manual
closure completed at 15:47:58 UTC: exact temporary IAM policy, two empty RDS
log groups, Scheduler and lease absent. Bootstrap remains; KMS and secrets
retain their deletion windows. The failed build and original report are kept;
the manual verification receipt does not claim pipeline success or zero cost.

The runner now checks authoritative service status for the observed NAT,
endpoint, security-group-rule, subnet, ECS cluster and Cognito pool references.
Unknown resource types remain active. Malformed responses, unexpected identity,
access denials and unrelated errors abort. Expected absence requires an exact
error code and operation. Inactive clusters must have no tasks or services;
deleting NAT/endpoints remain active. The NAT absent-code case includes the
provider's [NatGatewayNotFound handling](https://github.com/hashicorp/terraform-provider-aws/blob/v6.13.0/internal/service/ec2/find.go).
Eight regression tests failed before the fix; the complete offline suite then
passed 105 tests with nine integration skips. No real AWS mutation occurs in
these tests. Live closure is separate operational evidence, not a deployment
of the changed runner.

The first two PR CI attempts on `9b4730ad` failed one backend projection test,
while the branch push passed. The PR merge context included `develop` commit
`390721f9` (PR164), which added screen quantities to the response schema. The
branch has now incorporated that base. The old fixture derived its deliberately
small context budget from an empty screen, omitting this new essential schema;
the failure was reproduced locally after integrating the base. The fixture now
counts a one-row screen and its actual wire schema, retains a small allowance,
and asserts partial projection, explicit omissions and preservation of the
complete snapshot. No production context limits or application code are changed.
