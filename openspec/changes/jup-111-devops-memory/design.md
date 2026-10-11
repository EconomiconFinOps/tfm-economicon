JUP: JUP-111

## Context and scope

Section f belongs to JUP-111. Sources include JUP-051, JUP-052 and JUP-061;
container and observability claims additionally use JUP-049/050 and JUP-042–045.
The shared Google Doc remains the source of truth under docs/memoria/README.md.

## Decisions

- Refresh the technical source baseline to develop c3eb665, including integrated
  CD a0e9a56. Preserve the initial c2995a1/a75472d draft outside Git.
  Preserve the original date and environment of every reused runtime result.
- Keep nine proposal paragraphs outside Git with a coverage map across the
  brief's deliverables, technical/functional conditions and evaluation.
- Distinguish static CI checks, isolated Docker validation and automatic CD.
  Integrated promotion is supported by run 38136049444, matching a0e9a56 state
  and JUP-052 smoke evidence; independent readback confirms c3eb665/run
  38138774581. Reboot and production validation remain pending.
- Commit only the contract, evidence matrix and continuity. No memory prose,
  source document URL, whole-document export or credentials in this change.
- Independent subagent review precedes publishing under the explicit JUP-111
  deadline exception of 2026-10-11. Reconcile only the authorized section f
  fragment; do not read other sections for convenience. Final exports require
  the applicable reading authorizations and remain outside Git.

## Dependencies and limits

JUP-052 is integrated; distinguish observed automatic promotion from historical
local trials. JUP-062 governs publication with the documented role exception;
final style/page fit and independent acceptance remain pending. No ADR is ratified here and no service is deployed to fill a
documentary gap. Keep the change active until its publication tasks are met.

## Validation

Check source paths/hashes, figures and dates; inspect CD metadata and the actual
body of its latest functional review. Validate OpenSpec, JUP traceability,
repository hygiene and applicable governance tests. Negative checks reject
claims of automatic promotion based only on smoke/run_id=null or green CI.
