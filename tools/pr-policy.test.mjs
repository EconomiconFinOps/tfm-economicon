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

const SAME_REVIEWER = BODY.replace("- Validacion, pruebas y documentacion: Lucia", "- Validacion, pruebas y documentacion: Alejandro");
const DECLARED = `${SAME_REVIEWER}\n- Excepcion: revision y validacion por la misma persona, acordado en Trello\n`;
const policy = (body) =>
  checkPullRequest({ title: "chore(JUP-079): protect repository branches", body, head: "chore/JUP-079-branch-protection", base: "develop" });

test("accepts the same person in review and validation when the exception is declared", () => {
  assert.deepEqual(policy(DECLARED), []);
});

test("still requires four people when the exception is not declared", () => {
  assert.ok(policy(SAME_REVIEWER).some((error) => error.includes("cuatro personas distintas")));
});

test("does not accept a hidden exception line", () => {
  assert.ok(policy(`${SAME_REVIEWER}\n<!-- - Excepcion: revision y validacion por la misma persona, acordado en Trello -->\n`)
    .some((error) => error.includes("cuatro personas distintas")));
});

test("the exception never lets the leader or the pairing review or validate", () => {
  const leaderReviews = DECLARED.replace("- Revision de PR: Alejandro", "- Revision de PR: Paris").replace(
    "- Validacion, pruebas y documentacion: Alejandro",
    "- Validacion, pruebas y documentacion: Paris",
  );
  assert.ok(policy(leaderReviews).some((error) => error.includes("distintas")));
  const pairingReviews = DECLARED.replace("- Revision de PR: Alejandro", "- Revision de PR: Victor").replace(
    "- Validacion, pruebas y documentacion: Alejandro",
    "- Validacion, pruebas y documentacion: Victor",
  );
  assert.ok(policy(pairingReviews).some((error) => error.includes("distintas")));
});

test("rejects the exception line when review and validation name different people", () => {
  assert.ok(policy(`${BODY}\n- Excepcion: revision y validacion por la misma persona, acordado en Trello\n`)
    .some((error) => /excepcion/i.test(error)));
});

test("compares role names without accents or a leading @", () => {
  const accents = BODY.replace("- Revision de PR: Alejandro", "- Revision de PR: Ana María").replace(
    "- Validacion, pruebas y documentacion: Lucia",
    "- Validacion, pruebas y documentacion: Ana Maria",
  );
  assert.ok(policy(accents).some((error) => error.includes("cuatro personas distintas")));
  const handle = BODY.replace("- Validacion, pruebas y documentacion: Lucia", "- Validacion, pruebas y documentacion: @alejandro");
  assert.ok(policy(handle).some((error) => error.includes("cuatro personas distintas")));
});

test("the exception does not relax leadership and pairing", () => {
  const samePairing = DECLARED.replace("- Pairing/coautoria: Victor", "- Pairing/coautoria: Paris");
  assert.ok(policy(samePairing).some((error) => error.includes("distintas")));
});

test("an honest same-person pull request passes both checks", () => {
  const body = DECLARED.replace("- ID: JUP-079", "- ID: JUP-100");
  const title = "docs(JUP-100): flujo";
  const reviews = [
    { user: "Iber1to", state: "COMMENTED", body: "Revision JUP-100", submitted_at: "2026-09-30T10:00:00Z" },
    { user: "Iber1to", state: "APPROVED", body: "Validacion JUP-100", submitted_at: "2026-09-30T11:00:00Z" },
  ];
  assert.deepEqual(checkPullRequest({ title, body, head: "docs/JUP-100-flujo", base: "develop" }), []);
  assert.deepEqual(checkReviews({ title, body, author: "lmatsan", reviews }), []);
});

test("parses GitHub pull request events", () => {
  assert.deepEqual(
    parseEvent({ repository: { full_name: "EconomiconFinOps/tfm-economicon" }, pull_request: {
      number: 79, user: { login: "Iber1to" }, title: "JUP-079", body: BODY, head: { ref: "branch" }, base: { ref: "develop" },
    } }),
    { number: 79, repository: "EconomiconFinOps/tfm-economicon", author: "Iber1to", title: "JUP-079", body: BODY, head: "branch", base: "develop" },
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

test("dismissed titled reviews do not supply a required role", () => {
  assert.ok(checkReviews({ ...PR, reviews: [revision(), validacion("Iber1to", "DISMISSED")] })
    .some((error) => error.includes("Validacion JUP-100")));
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
  const errors = checkReviews({ ...PR, reviews });
  assert.ok(errors.some((error) => error.includes("Revision JUP-100")));
  assert.ok(!errors.some((error) => /cambios pedidos/.test(error)));
});

test("an approval dismissed by a push does not revive an older request for changes", () => {
  const reviews = [
    revision("Victorh1397", "CHANGES_REQUESTED"),
    review("Victorh1397", "DISMISSED", "ok, resuelto"),
    validacion(),
  ];
  assert.deepEqual(checkReviews({ ...PR, reviews }), []);
});

test("compares reviewer logins without case when finding the latest decision", () => {
  const reviews = [revision("Victorh1397", "CHANGES_REQUESTED"), validacion(), review("victorh1397", "APPROVED", "ok")];
  assert.deepEqual(checkReviews({ ...PR, reviews }), []);
});

test("an exception line hidden inside an HTML comment does not count", () => {
  const reviews = [revision("Victorh1397"), validacion("Victorh1397")];
  const hidden = `${BODY}\n<!--\n${EXCEPTION.trim()}\n-->\n`;
  assert.ok(checkReviews({ ...PR, body: hidden, reviews }).some((e) => /misma persona/i.test(e)));
});

test("the exception line must be complete, not just a prefix", () => {
  const reviews = [revision("Victorh1397"), validacion("Victorh1397")];
  const negated = `${BODY}\n- Excepcion: revision y validacion por la misma persona, acordado en Trello: NO\n`;
  assert.ok(checkReviews({ ...PR, body: negated, reviews }).some((e) => /misma persona/i.test(e)));
  const withPeriod = `${BODY}\n- Excepcion: revision y validacion por la misma persona, acordado en Trello.\n`;
  assert.deepEqual(checkReviews({ ...PR, body: withPeriod, reviews }), []);
});

test("an exception line inside a code block does not count", () => {
  const reviews = [revision("Victorh1397"), validacion("Victorh1397")];
  const fenced = `${BODY}\n\`\`\`\n${EXCEPTION.trim()}\n\`\`\`\n`;
  assert.ok(checkReviews({ ...PR, body: fenced, reviews }).some((e) => /misma persona/i.test(e)));
});

test("an exception line that GitHub would not show as plain text does not count", () => {
  const reviews = [revision("Victorh1397"), validacion("Victorh1397")];
  const line = EXCEPTION.trim();
  const hidden = {
    "unclosed comment": `${BODY}\n<!-- nota\n${line}\n`,
    "tilde fence": `${BODY}\n~~~\n${line}\n~~~\n`,
    "indented fence": `${BODY}\n  \`\`\`\n  ${line}\n  \`\`\`\n`,
    "indented code": `${BODY}\ntexto\n\n    ${line}\n`,
  };
  for (const [name, body] of Object.entries(hidden)) {
    assert.ok(checkReviews({ ...PR, body, reviews }).some((e) => /misma persona/i.test(e)), name);
  }
});

test("asks for the exception whenever someone published both titled reviews", () => {
  const reviews = [revision("Victorh1397"), validacion("Victorh1397"), review("ParisArcos", "COMMENTED", "Revision JUP-100\nok")];
  assert.ok(checkReviews({ ...PR, reviews }).some((e) => /misma persona/i.test(e)));
});

test("every error links to the flow with a clickable URL", () => {
  const cases = [
    { ...PR, title: "sin identificador", reviews: [] },
    { ...PR, reviews: [] },
    { ...PR, reviews: [revision("Victorh1397", "CHANGES_REQUESTED"), validacion("Victorh1397")] },
  ];
  for (const input of cases) {
    for (const error of checkReviews(input)) {
      assert.match(error, /https:\/\/github\.com\/EconomiconFinOps\/tfm-economicon\/blob\/develop\/CONTRIBUTING\.md#review-and-validation-flow/, error);
    }
  }
});

test("explains that the title must be the plain first line", () => {
  const reviews = [review("Victorh1397", "COMMENTED", "## Revision JUP-100"), validacion()];
  assert.ok(checkReviews({ ...PR, reviews }).some((e) => /primera linea/i.test(e)));
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
  assert.match(result.stderr, /CONTRIBUTING\.md#review-and-validation-flow/);
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
  assert.match(result.stderr, /CONTRIBUTING\.md#review-and-validation-flow/);
});

test("fails instead of passing when the API cannot be read", async () => {
  await assert.rejects(fetchReviewInput({ repository: REPO, number: 100, token: "t", fetchImpl: fakeFetch({}) }), /404/);
  await assert.rejects(
    fetchReviewInput({ repository: REPO, number: 100, token: "t", fetchImpl: fakeFetch({ "/pulls/100": new Error("network down") }) }),
    /network down/,
  );
});

test("the --reviews command shows its errors as annotations in GitHub Actions", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "jup-reviews-"));
  const eventPath = path.join(dir, "event.json");
  fs.writeFileSync(eventPath, JSON.stringify({ pull_request: { number: 100 } }));
  const run = (actions) => {
    const env = { ...process.env, GITHUB_REPOSITORY: REPO };
    delete env.GITHUB_TOKEN;
    if (actions) env.GITHUB_ACTIONS = "true";
    else delete env.GITHUB_ACTIONS;
    return spawnSync(process.execPath, [fileURLToPath(new URL("./pr-policy.mjs", import.meta.url)), "--reviews", "--event", eventPath], { encoding: "utf8", env });
  };
  const inActions = run(true);
  const local = run(false);
  fs.rmSync(dir, { recursive: true, force: true });
  assert.equal(inActions.status, 1);
  assert.match(inActions.stdout, /^::error title=JUP reviews::Falta GITHUB_TOKEN.*CONTRIBUTING\.md#review-and-validation-flow$/m);
  assert.doesNotMatch(local.stdout, /::error/);
});


test("PR63: a dismissed validation and complementary review do not invent an exception", () => {
  const reviews = [validacion("helper", "DISMISSED"), revision("reviewer"),
    validacion("validator"), revision("helper")];
  assert.deepEqual(checkReviews({ ...PR, reviews }), []);
});

test("a dismissed latest title does not revive the person's older title", () => {
  const reviews = [revision(), validacion(), validacion("Iber1to", "DISMISSED")];
  assert.ok(checkReviews({ ...PR, reviews }).some((error) => error.includes("Validacion JUP-100")));
});

test("a new title after dismissal restores that role", () => {
  const reviews = [revision(), validacion("Iber1to", "DISMISSED"), validacion()];
  assert.deepEqual(checkReviews({ ...PR, reviews }), []);
});

test("complementary outstanding change requests still block the official pair", () => {
  const reviews = [revision(), validacion(), review("helper", "CHANGES_REQUESTED", "Defecto"),
    review("helper", "COMMENTED", "Sigue pendiente")];
  assert.ok(checkReviews({ ...PR, reviews }).some((error) => error.includes("helper")));
});


test("PR63 recorded title/state metadata no longer demands an invented exception", () => {
  const input = JSON.parse(fs.readFileSync(new URL("./fixtures/pr-reviews/pr63-20261016.json", import.meta.url), "utf8"));
  assert.equal(input.reviews.length, 18);
  assert.deepEqual(checkReviews(input), []);
});

test("latest title selection uses date, normalized login and review kind", () => {
  const oldValidation = validacion("IBER1TO");
  const dismissed = review("iber1to", "DISMISSED", "Validación JUP-100");
  const errors = checkReviews({ ...PR, reviews: [dismissed, revision(), oldValidation] });
  assert.ok(errors.some((error) => error.includes("Validacion JUP-100")));
});

// Literal authorization is deliberately independent of the implementation's
// exported marker: changing a guard/marker must not change the expected case.
const PR135_MARKER = "- Excepcion puntual PR135: pairing y revision por Lucia Mateo; validacion por Paris Arcos Martin; autorizada por Alejandro Aguado el 2026-10-18";
const PR135_BODY = `- ID: JUP-126
- Trello: https://trello.com/c/SplMvNMA
- Liderazgo: Alejandro Aguado
- Pairing/coautoria: Lucia Mateo
- Revision de PR: Lucia Mateo
- Validacion, pruebas y documentacion: Paris Arcos Martin
${PR135_MARKER}
`;
let pr135Sequence = 0;
const pr135Review = (user, state, body) => ({ user, state, body,
  submitted_at: new Date(Date.UTC(2026, 9, 18, 12, pr135Sequence++)).toISOString() });
const PR135_REVIEWS = [
  pr135Review("ParisArcos", "COMMENTED", "Revision JUP-126\nHistorical review, retained."),
  pr135Review("lmatsan", "COMMENTED", "Revision JUP-126\nCurrent assigned review."),
  pr135Review("ParisArcos", "APPROVED", "Validacion JUP-126\nIndependent validation evidence."),
];
const PR135 = { number: 135, repository: REPO, author: "Iber1to", title: "fix(JUP-126): dismissed titles",
  body: PR135_BODY, head: "fix/JUP-126-dismissed-review-titles", base: "develop", reviews: PR135_REVIEWS };
const rejectPr135 = (input) => {
  assert.notDeepEqual(checkPullRequest(input), [], "role policy must fail closed");
  assert.notDeepEqual(checkReviews(input), [], "review policy must fail closed");
};

test("PR135 authorization accepts only the approved allocation with both assigned titles", () => {
  assert.deepEqual(checkPullRequest(PR135), []);
  assert.deepEqual(checkReviews(PR135), []);
  assert.equal(PR135_REVIEWS[0].state, "COMMENTED", "history is not dismissed or mutated");
});

for (const [name, change] of [
  ["another PR number", { number: 136 }], ["PR63", { number: 63 }],
  ["missing PR number", { number: undefined }], ["string PR number", { number: "135" }],
  ["another repository", { repository: "other/tfm-economicon" }],
  ["another author", { author: "lmatsan" }],
  ["another card", { title: "fix(JUP-127): other", body: PR135_BODY.replace("ID: JUP-126", "ID: JUP-127") }],
  ["main", { base: "main", head: "develop" }],
  ["another branch", { head: "fix/JUP-126-other" }],
]) {
  test(`PR135 authorization rejects ${name}`, () => rejectPr135({ ...PR135, ...change }));
}

for (const label of ["Liderazgo", "Pairing/coautoria", "Revision de PR", "Validacion, pruebas y documentacion"]) {
  test(`PR135 authorization rejects a different ${label}`, () => {
    const changed = PR135_BODY.replace(new RegExp(`^- ${label}:.*$`, "m"), `- ${label}: Victor Mendez`);
    rejectPr135({ ...PR135, body: changed });
  });
}

test("PR135 authorization rejects duplicate roles or declarations", () => {
  rejectPr135({ ...PR135, body: PR135_BODY + "- Liderazgo: Victor Mendez\n" });
  rejectPr135({ ...PR135, body: PR135_BODY + PR135_MARKER + "\n" });
  const changed = PR135_BODY.replace("- Liderazgo: Alejandro Aguado", "- Liderazgo: Victor Mendez");
  rejectPr135({ ...PR135, body: "<!--\n- Liderazgo: Alejandro Aguado\n-->\n" + changed });
});

for (const [name, wrap] of [
  ["missing marker", () => ""], ["HTML comment", (x) => `<!--\n${x}\n-->`],
  ["unclosed comment", (x) => `<!--\n${x}`], ["backtick fence", (x) => "```md\n" + x + "\n```"],
  ["tilde fence", (x) => "~~~\n" + x + "\n~~~"], ["unclosed fence", (x) => "```\n" + x],
  ["short inner fence", (x) => "````\n```\n" + x + "\n````"],
  ["indented code", (x) => "    " + x], ["tab code", (x) => "\t" + x],
  ["inline code", (x) => "`" + x + "`"], ["quote", (x) => "> " + x],
  ["multiline code span", (x) => "`example\n" + x + "\nend`"],
  ["double-backtick code span", (x) => "``example `\n" + x + "\nend``"],
  ["HTML code", (x) => `<pre><code>\n${x}\n</code></pre>`],
  ["hidden HTML", (x) => `<div hidden>\n${x}\n</div>`],
  ["different authorization date", (x) => x.replace("2026-10-18", "2026-10-19")],
  ["altered authorization text", (x) => x.replace("Excepcion puntual", "excepcion puntual")],
]) {
  test(`PR135 authorization rejects ${name}`, () => {
    rejectPr135({ ...PR135, body: PR135_BODY.replace(PR135_MARKER, wrap(PR135_MARKER)) });
  });
}

test("PR135 authorization does not accept roles hidden in code", () => {
  const roles = PR135_BODY.slice(PR135_BODY.indexOf("- Liderazgo:"), PR135_BODY.indexOf(PR135_MARKER));
  rejectPr135({ ...PR135, body: PR135_BODY.replace(roles, "```\n" + roles + "```\n") });
});

test("PR135 authorization ignores a code-span example when the visible declaration also exists", () => {
  assert.deepEqual(checkPullRequest({ ...PR135, body: PR135_BODY + "\n`example\n" + PR135_MARKER + "\nend`\n" }), []);
});

test("PR135 authorization keeps title/role login matching case insensitive", () => {
  const reviews = PR135_REVIEWS.map((r) => ({ ...r, user: r.user.toUpperCase() }));
  assert.deepEqual(checkReviews({ ...PR135, reviews }), []);
});

test("PR135 authorization requires the assigned review and validation separately", () => {
  const [historical, revision135, validation135] = PR135_REVIEWS;
  assert.match(checkReviews({ ...PR135, reviews: [historical, validation135] }).join(), /Revision JUP-126/);
  assert.match(checkReviews({ ...PR135, reviews: [historical, revision135] }).join(), /Validacion JUP-126/);
  const wrongValidation = pr135Review("Victorh1397", "APPROVED", "Validacion JUP-126");
  assert.match(checkReviews({ ...PR135, reviews: [historical, revision135, wrongValidation] }).join(), /Validacion JUP-126/);
  const wrongCard = { ...validation135, body: "Validacion JUP-1260" };
  assert.match(checkReviews({ ...PR135, reviews: [historical, revision135, wrongCard] }).join(), /Validacion JUP-126/);
});

test("PR135 authorization excludes author and draft titles", () => {
  for (const index of [1, 2]) {
    for (const change of [{ user: "Iber1to" }, { state: "PENDING" }]) {
      const reviews = PR135_REVIEWS.map((r, i) => i === index ? { ...r, ...change } : r);
      assert.notDeepEqual(checkReviews({ ...PR135, reviews }), []);
    }
  }
});

test("PR135 authorization selects latest assigned titles before excluding dismissals", () => {
  const dismissed = pr135Review("ParisArcos", "DISMISSED", "Validacion JUP-126");
  const reviews = [...PR135_REVIEWS, dismissed];
  assert.match(checkReviews({ ...PR135, reviews }).join(), /Validacion JUP-126/);
  const fresh = pr135Review("ParisArcos", "APPROVED", "Validacion JUP-126");
  assert.deepEqual(checkReviews({ ...PR135, reviews: [...reviews, fresh] }), []);
});

test("PR135 authorization retains complete decisive history including complementary changes", () => {
  const changes = pr135Review("helper", "CHANGES_REQUESTED", "Revision JUP-126\nBlocking issue.");
  const comment = pr135Review("helper", "COMMENTED", "Not resolved.");
  const reviews = [...PR135_REVIEWS, changes, comment];
  assert.match(checkReviews({ ...PR135, reviews }).join(), /cambios pedidos pendientes de helper/);
  const approved = pr135Review("helper", "APPROVED", "Resolved.");
  const dismissed = pr135Review("helper", "DISMISSED", "Resolved approval dismissed.");
  assert.deepEqual(checkReviews({ ...PR135, reviews: [...reviews, approved, dismissed] }), []);
  const parisChanges = pr135Review("ParisArcos", "CHANGES_REQUESTED", "Blocking issue.");
  const parisComment = pr135Review("ParisArcos", "COMMENTED", "Validacion JUP-126\nStill blocked.");
  assert.match(checkReviews({ ...PR135, reviews: [...PR135_REVIEWS, parisChanges, parisComment] }).join(), /cambios pedidos pendientes de ParisArcos/);
});

test("PR135 authorization preserves the ordinary overlap rule without its declaration", () => {
  const body = PR135_BODY.replace(PR135_MARKER, "");
  assert.match(checkReviews({ ...PR135, body }).join(), /misma persona/);
  assert.match(checkPullRequest({ ...PR135, body }).join(), /cuatro personas distintas/);
});

test("PR135 authorization receives authoritative identity from event and live API", async () => {
  const pull = { number: 135, title: PR135.title, body: PR135_BODY, user: { login: "Iber1to" },
    head: { ref: PR135.head }, base: { ref: "develop" } };
  const eventInput = parseEvent({ repository: { full_name: REPO }, pull_request: pull });
  assert.deepEqual(checkPullRequest(eventInput), []);
  const routes = { "/pulls/135": pull, "/pulls/135/reviews?per_page=100&page=1":
    PR135_REVIEWS.map(({ user, ...rest }) => ({ user: { login: user }, ...rest })) };
  const live = await fetchReviewInput({ repository: REPO, number: 135, token: "t", fetchImpl: fakeFetch(routes) });
  assert.equal(live.number, 135);
  assert.equal(live.repository, REPO);
  assert.equal(live.head, PR135.head);
  assert.deepEqual(checkPullRequest(live), []);
  assert.deepEqual(checkReviews(live), []);
  const { number, ...withoutNumber } = pull;
  routes["/pulls/135"] = withoutNumber;
  const missing = await fetchReviewInput({ repository: REPO, number: 135, token: "t", fetchImpl: fakeFetch(routes) });
  rejectPr135(missing); // A caller-supplied number is not a substitute for API metadata.
});
