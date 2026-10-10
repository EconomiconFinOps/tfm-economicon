JUP: JUP-111

## Context and scope

Section f belongs to JUP-111. Sources include JUP-051, JUP-052 and JUP-061;
container and observability claims additionally use JUP-049/050 and JUP-042–045.
The shared Google Doc remains the source of truth under docs/memoria/README.md.

## Decisions

- Fix the technical source baseline to develop c2995a1 and CD candidate a75472d.
  Preserve the original date and environment of every reused runtime result.
- Keep nine proposal paragraphs outside Git with a coverage map across the
  brief's deliverables, technical/functional conditions and evaluation.
- Distinguish static CI checks, isolated Docker validation and automatic CD.
  First integrated promotion remains pending until matching SHA/run/state and
  functional evidence exist.
- Commit only the contract, evidence matrix and continuity. No memory prose,
  source document URL, whole-document export or credentials in this change.
- Human review precedes publishing. Reconcile only the authorized section f
  fragment; do not read other sections for convenience. Final exports require
  the applicable reading authorizations and remain outside Git.

## Dependencies and limits

JUP-052 remains open; its missing deployment evidence does not block an honest
draft. JUP-062 governs publication; final style/page fit and human participation
remain pending. No ADR is ratified here and no service is deployed to fill a
documentary gap. Keep the change active until its publication tasks are met.

## Validation

Check source paths/hashes, figures and dates; inspect CD metadata and the actual
body of its latest functional review. Validate OpenSpec, JUP traceability,
repository hygiene and applicable governance tests. Negative checks reject
claims of automatic promotion based only on smoke/run_id=null or green CI.
