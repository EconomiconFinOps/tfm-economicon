import assert from "node:assert/strict";
import test from "node:test";

import { checkPullRequest, parseEvent } from "./pr-policy.mjs";

const BODY = `## JUP
- ID: JUP-079
- Trello: https://trello.com/c/10RWrMCS

## Participacion

- Liderazgo: Paris
- Pairing/coautoria: Victor
- Revision de PR: Alejandro
- Validacion, pruebas y documentacion: Lucia
`;

test("accepts a JUP branch targeting develop", () => {
  assert.deepEqual(
    checkPullRequest({
      title: "chore(JUP-079): protect repository branches",
      body: BODY,
      head: "chore/JUP-079-branch-protection",
      base: "develop",
    }),
    [],
  );
});

test("accepts only develop as source for main", () => {
  assert.deepEqual(
    checkPullRequest({ title: "release(JUP-079): promote develop", body: BODY, head: "develop", base: "main" }),
    [],
  );
  assert.ok(
    checkPullRequest({ title: "fix(JUP-079): bypass", body: BODY, head: "fix/JUP-079-bypass", base: "main" })
      .some((error) => error.includes("Solo develop")),
  );
});

test("rejects mismatched JUP identifiers", () => {
  const errors = checkPullRequest({
    title: "fix(JUP-080): mismatch",
    body: BODY,
    head: "fix/JUP-079-mismatch",
    base: "develop",
  });
  assert.ok(errors.some((error) => error.includes("debe coincidir")));
});

test("rejects an invalid branch and unsupported base", () => {
  const errors = checkPullRequest({ title: "JUP-079 invalid", body: BODY, head: "random", base: "release" });
  assert.ok(errors.some((error) => error.includes("base")));
});

test("requires a direct Trello card URL", () => {
  const errors = checkPullRequest({
    title: "JUP-079 missing Trello",
    body: BODY.replace("https://trello.com/c/10RWrMCS", "Trello pendiente"),
    head: "chore/JUP-079-branch-protection",
    base: "develop",
  });
  assert.ok(errors.some((error) => error.includes("Trello")));
});

test("requires every rotating role to be filled", () => {
  const errors = checkPullRequest({
    title: "JUP-079 missing role",
    body: BODY.replace("- Revision de PR: Alejandro", "- Revision de PR: pendiente"),
    head: "chore/JUP-079-branch-protection",
    base: "develop",
  });
  assert.ok(errors.some((error) => error.includes("Revision de PR")));
});

test("parses GitHub pull request events", () => {
  assert.deepEqual(
    parseEvent({ pull_request: { title: "JUP-079", body: BODY, head: { ref: "branch" }, base: { ref: "develop" } } }),
    { title: "JUP-079", body: BODY, head: "branch", base: "develop" },
  );
});

test("rejects non pull-request events", () => {
  assert.throws(() => parseEvent({}), /pull_request/);
});
