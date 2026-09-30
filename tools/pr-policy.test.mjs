import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { checkPullRequest, checkReviews, fetchReviewInput, parseEvent } from "./pr-policy.mjs";

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

test("requires the body identifier to match the title and branch", () => {
  const errors = checkPullRequest({
    title: "chore(JUP-079): protect repository branches",
    body: BODY.replace("- ID: JUP-079", "- ID: JUP-080"),
    head: "chore/JUP-079-branch-protection",
    base: "develop",
  });

  assert.ok(errors.some((error) => error.includes("cuerpo y el titulo")));
});

test("rejects a missing body identifier", () => {
  const errors = checkPullRequest({
    title: "chore(JUP-079): protect repository branches",
    body: BODY.replace("- ID: JUP-079", "- ID: pendiente"),
    head: "chore/JUP-079-branch-protection",
    base: "develop",
  });

  assert.ok(errors.some((error) => error.includes("cuerpo debe identificar")));
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

test("requires four different people across the rotating roles", () => {
  const errors = checkPullRequest({
    title: "chore(JUP-079): protect repository branches",
    body: BODY.replace("- Revision de PR: Alejandro", "- Revision de PR: Paris"),
    head: "chore/JUP-079-branch-protection",
    base: "develop",
  });

  assert.ok(errors.some((error) => error.includes("cuatro personas distintas")));
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

const PR = { title: "docs(JUP-100): flujo de revision", body: BODY, author: "lmatsan", base: "develop" };
let clock = 0;
const review = (user, state, text) => ({
  user,
  state,
  body: text,
  submitted_at: new Date(Date.UTC(2026, 8, 30, 10, clock++)).toISOString(),
});
const revision = (user = "Victorh1397", state = "COMMENTED") => review(user, state, "Revision JUP-100\n\nVerificado: ...");
const validacion = (user = "Iber1to", state = "APPROVED") => review(user, state, "Validacion JUP-100\n\n- [x] criterio");
const EXCEPTION = "\n- Excepcion: revision y validacion por la misma persona, acordado en Trello\n";

test("accepts a review and a validation from people other than the author", () => {
  assert.deepEqual(checkReviews({ ...PR, reviews: [revision(), validacion()] }), []);
});

test("names the missing validation and links the flow", () => {
  const errors = checkReviews({ ...PR, reviews: [revision()] });
  assert.equal(errors.length, 1);
  assert.match(errors[0], /Validacion JUP-100/);
  assert.match(errors[0], /CONTRIBUTING\.md#/);
});

test("names the missing review and links the flow", () => {
  const errors = checkReviews({ ...PR, reviews: [validacion()] });
  assert.equal(errors.length, 1);
  assert.match(errors[0], /Revision JUP-100/);
  assert.match(errors[0], /CONTRIBUTING\.md#/);
});

test("reports both titled reviews when none exists", () => {
  const errors = checkReviews({ ...PR, reviews: [] });
  assert.ok(errors.some((e) => e.includes("Revision JUP-100")));
  assert.ok(errors.some((e) => e.includes("Validacion JUP-100")));
});

test("accepts accented and lowercase titles in both reviews", () => {
  const reviews = [
    review("Victorh1397", "COMMENTED", "revisión jup-100\nok"),
    review("Iber1to", "APPROVED", "VALIDACIÓN JUP-100\nok"),
  ];
  assert.deepEqual(checkReviews({ ...PR, reviews }), []);
});

test("accepts accents written as separate combining characters", () => {
  const reviews = [
    review("Victorh1397", "COMMENTED", "Revisión JUP-100"),
    review("Iber1to", "APPROVED", "Validación JUP-100"),
  ];
  assert.deepEqual(checkReviews({ ...PR, reviews }), []);
});

test("accepts leading blank lines before the title", () => {
  const reviews = [review("Victorh1397", "COMMENTED", "\n  Revision JUP-100"), validacion()];
  assert.deepEqual(checkReviews({ ...PR, reviews }), []);
});

test("ignores titles that are not at the start of the review", () => {
  const reviews = [review("Victorh1397", "COMMENTED", "Nota: Revision JUP-100"), validacion()];
  assert.ok(checkReviews({ ...PR, reviews }).some((e) => e.includes("Revision JUP-100")));
});

test("does not count titles for another card or a longer identifier", () => {
  for (const title of ["Validacion JUP-026", "Validacion JUP-1000", "Validacion JUP-10"]) {
    const reviews = [revision(), review("Iber1to", "APPROVED", title)];
    assert.ok(
      checkReviews({ ...PR, reviews }).some((e) => e.includes("Validacion JUP-100")),
      title,
    );
  }
});

test("does not count words that only start like the title", () => {
  const reviews = [review("Victorh1397", "COMMENTED", "Revisiones JUP-100"), validacion()];
  assert.ok(checkReviews({ ...PR, reviews }).some((e) => e.includes("Revision JUP-100")));
});

test("ignores reviews from the author, whatever the login casing", () => {
  for (const author of ["Iber1to", "iber1to", "IBER1TO"]) {
    const errors = checkReviews({ ...PR, author, reviews: [revision(), validacion("Iber1to")] });
    assert.ok(errors.some((e) => e.includes("Validacion JUP-100")), author);
  }
});

test("ignores pending draft reviews", () => {
  const errors = checkReviews({ ...PR, reviews: [revision(), validacion("Iber1to", "PENDING")] });
  assert.ok(errors.some((e) => e.includes("Validacion JUP-100")));
});

test("still counts dismissed titled reviews", () => {
  assert.deepEqual(checkReviews({ ...PR, reviews: [revision(), validacion("Iber1to", "DISMISSED")] }), []);
});

test("blocks while a reviewer's latest decisive review requests changes", () => {
  const errors = checkReviews({ ...PR, reviews: [revision("Victorh1397", "CHANGES_REQUESTED"), validacion()] });
  assert.ok(errors.some((e) => e.includes("Victorh1397") && /cambios/i.test(e)));
});

test("a later approval by the same reviewer clears the request", () => {
  const reviews = [revision("Victorh1397", "CHANGES_REQUESTED"), validacion(), review("Victorh1397", "APPROVED", "ok")];
  assert.deepEqual(checkReviews({ ...PR, reviews }), []);
});

test("a later comment does not clear a request for changes", () => {
  const reviews = [revision("Victorh1397", "CHANGES_REQUESTED"), validacion(), review("Victorh1397", "COMMENTED", "visto")];
  assert.ok(checkReviews({ ...PR, reviews }).some((e) => e.includes("Victorh1397")));
});

test("a dismissed request for changes no longer blocks", () => {
  const reviews = [revision("Victorh1397", "DISMISSED"), validacion()];
  assert.deepEqual(checkReviews({ ...PR, reviews }), []);
});

test("a request for changes from someone outside the two roles also blocks", () => {
  const reviews = [revision(), validacion(), review("ParisArcos", "CHANGES_REQUESTED", "Falta X")];
  assert.ok(checkReviews({ ...PR, reviews }).some((e) => e.includes("ParisArcos")));
});

test("uses submission time, not list order, to find the latest decisive review", () => {
  const requested = review("Victorh1397", "CHANGES_REQUESTED", "Revision JUP-100\nfalta");
  const approved = review("Victorh1397", "APPROVED", "ok");
  assert.deepEqual(checkReviews({ ...PR, reviews: [approved, validacion(), requested] }), []);

  const approvedFirst = review("ParisArcos", "APPROVED", "ok");
  const requestedLater = review("ParisArcos", "CHANGES_REQUESTED", "falta");
  const reviews = [requestedLater, revision(), validacion(), approvedFirst];
  assert.ok(checkReviews({ ...PR, reviews }).some((e) => e.includes("ParisArcos")));
});

test("the same person needs an explicit exception in the description", () => {
  const reviews = [revision("Victorh1397"), validacion("victorh1397")];
  assert.ok(checkReviews({ ...PR, reviews }).some((e) => /misma persona/i.test(e) && e.includes("CONTRIBUTING.md#")));
  assert.deepEqual(checkReviews({ ...PR, body: BODY + EXCEPTION, reviews }), []);
  const accented = EXCEPTION.replace("Excepcion", "Excepción").replace("revision y validacion", "revisión y validación");
  assert.deepEqual(checkReviews({ ...PR, body: BODY + accented, reviews }), []);
});

test("the pull request template does not declare the exception by itself", () => {
  const template = fs.readFileSync(new URL("../.github/pull_request_template.md", import.meta.url), "utf8");
  const reviews = [revision("Victorh1397"), validacion("Victorh1397")];
  assert.ok(checkReviews({ ...PR, body: BODY + template, reviews }).some((e) => /misma persona/i.test(e)));
});

test("reports the missing exception and pending changes together", () => {
  const reviews = [revision("Victorh1397", "CHANGES_REQUESTED"), validacion("Victorh1397", "COMMENTED")];
  const errors = checkReviews({ ...PR, reviews });
  assert.ok(errors.some((e) => /misma persona/i.test(e)));
  assert.ok(errors.some((e) => /cambios/i.test(e)));
});

test("applies the same rules to release pull requests towards main", () => {
  const release = { ...PR, title: "release(JUP-100): promote develop", base: "main" };
  assert.deepEqual(checkReviews({ ...release, reviews: [revision("Victorh1397", "APPROVED"), validacion()] }), []);
  assert.ok(checkReviews({ ...release, reviews: [validacion()] }).some((e) => e.includes("Revision JUP-100")));
});

test("fails when the title has no JUP identifier", () => {
  const errors = checkReviews({ ...PR, title: "sin identificador", reviews: [revision(), validacion()] });
  assert.ok(errors.some((e) => e.includes("JUP-XXX")));
});

const fakeFetch = (routes) => async (url) => {
  const hit = Object.entries(routes).find(([key]) => url.endsWith(key));
  if (!hit) return { ok: false, status: 404, json: async () => ({}) };
  if (hit[1] instanceof Error) throw hit[1];
  return { ok: true, status: 200, json: async () => hit[1] };
};
const PULL = { title: PR.title, body: BODY, user: { login: "lmatsan" }, base: { ref: "develop" } };
const REPO = "EconomiconFinOps/tfm-economicon";

test("reads the pull request and every review page from the API", async () => {
  const first = Array.from({ length: 100 }, () => ({ user: { login: "ParisArcos" }, state: "COMMENTED", body: "nota", submitted_at: "2026-09-30T10:00:00Z" }));
  const last = { user: { login: "Iber1to" }, state: "APPROVED", body: "Validacion JUP-100", submitted_at: "2026-09-30T11:00:00Z" };
  const input = await fetchReviewInput({
    repository: REPO,
    number: 100,
    token: "t",
    fetchImpl: fakeFetch({
      "/pulls/100": PULL,
      "/pulls/100/reviews?per_page=100&page=1": first,
      "/pulls/100/reviews?per_page=100&page=2": [last],
    }),
  });
  assert.equal(input.author, "lmatsan");
  assert.equal(input.base, "develop");
  assert.equal(input.reviews.length, 101);
  assert.deepEqual(input.reviews.at(-1), { user: "Iber1to", state: "APPROVED", body: "Validacion JUP-100", submitted_at: "2026-09-30T11:00:00Z" });
});

test("the --reviews command fails with a clear message when GitHub cannot be reached", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "jup-reviews-"));
  const eventPath = path.join(dir, "event.json");
  fs.writeFileSync(eventPath, JSON.stringify({ pull_request: { number: 100 } }));
  const result = spawnSync(process.execPath, [fileURLToPath(new URL("./pr-policy.mjs", import.meta.url)), "--reviews", "--event", eventPath], {
    encoding: "utf8",
    env: { ...process.env, GITHUB_REPOSITORY: REPO, GITHUB_TOKEN: "t", GITHUB_API_URL: "http://127.0.0.1:9" },
  });
  fs.rmSync(dir, { recursive: true, force: true });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /No se pudieron leer las reviews/);
  assert.doesNotMatch(result.stdout, /\[OK\]/);
});

test("the --reviews command refuses to run without a token", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "jup-reviews-"));
  const eventPath = path.join(dir, "event.json");
  fs.writeFileSync(eventPath, JSON.stringify({ pull_request: { number: 100 } }));
  const env = { ...process.env, GITHUB_REPOSITORY: REPO };
  delete env.GITHUB_TOKEN;
  const result = spawnSync(process.execPath, [fileURLToPath(new URL("./pr-policy.mjs", import.meta.url)), "--reviews", "--event", eventPath], { encoding: "utf8", env });
  fs.rmSync(dir, { recursive: true, force: true });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /GITHUB_TOKEN/);
});

test("fails instead of passing when the API cannot be read", async () => {
  await assert.rejects(fetchReviewInput({ repository: REPO, number: 100, token: "t", fetchImpl: fakeFetch({}) }), /404/);
  await assert.rejects(
    fetchReviewInput({ repository: REPO, number: 100, token: "t", fetchImpl: fakeFetch({ "/pulls/100": new Error("network down") }) }),
    /network down/,
  );
});
