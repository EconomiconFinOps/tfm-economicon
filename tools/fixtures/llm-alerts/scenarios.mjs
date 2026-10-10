// Deterministic synthetic complete-call counters. Promtool evaluates PromQL;
// this module only constructs samples and independent expected alert states.
export const bucketBounds = [0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 30, 60, 120, "+Inf"];
const ids = ["llm-provider-error-ratio", "llm-embedding-latency", "llm-generation-latency"];
const base = { job: "backend", instance: "backend:8000", operation: "embedding" };
const fixedLabels = { severity: "warning", component: "llm", jup: "JUP-046" };

function selector(metric, labels) {
  return `${metric}{${Object.entries(labels).map(([key, value]) => `${key}=${JSON.stringify(value)}`).join(",")}}`;
}

function requests(outcome, values, labels = base) {
  return {
    series: selector("llm_provider_requests_total", {
      ...labels, outcome, category: outcome === "success" ? "none" : "timeout",
    }),
    values,
  };
}

function histogram(labels, countAtBucket, values = (count) => `0+${count}x12`) {
  return bucketBounds.map((le) => ({
    series: selector("llm_provider_request_duration_seconds_bucket", { ...labels, le: String(le) }),
    values: values(countAtBucket(le === "+Inf" ? Infinity : le)),
  }));
}

function expected(labels = base) {
  return { exp_labels: { ...labels, ...fixedLabels } };
}

function alertAt(alertname, eval_time, firing = []) {
  return { eval_time, alertname, exp_alerts: firing.map(expected) };
}

function sample(labels, value) {
  return { labels: selector("", labels), value };
}

function scenario(name, input_series, alert_rule_test, promql_expr_test = []) {
  return { name, interval: "1m", input_series, alert_rule_test, promql_expr_test };
}

export function createScenarios(expressions) {
  const queryAt = (uid, eval_time, samples) => ({ expr: expressions[uid], eval_time, exp_samples: samples });
  const allQuiet = (time = "10m") => ids.map((id) => alertAt(id, time));
  const generation = { ...base, operation: "generation" };
  const tests = [
    scenario("success-only traffic is Normal even without a failure label set", [
      requests("success", "0+10x12"),
    ], allQuiet(), [queryAt(ids[0], "10m", [sample(base, 0)])]),
    scenario("exactly twenty percent errors does not breach strict threshold", [
      requests("success", "0+8x12"), requests("failure", "0+2x12"),
    ], allQuiet(), [queryAt(ids[0], "10m", [sample(base, 0)])]),
    scenario("sustained errors fire only after the two minute pending period", [
      requests("success", "0+6x12"), requests("failure", "0+4x12"),
    ], [alertAt(ids[0], "2m"), alertAt(ids[0], "3m", [base])], [
      queryAt(ids[0], "2m", [sample(base, 1)]),
    ]),
    scenario("fewer than five extrapolated calls suppress even total failure", [
      requests("failure", "0+0.8x12"),
    ], allQuiet(), [queryAt(ids[0], "10m", [sample(base, 0)])]),
    scenario("exactly five extrapolated calls enable the error gate", [
      requests("failure", "0+1x12"),
    ], [alertAt(ids[0], "5m"), alertAt(ids[0], "6m"), alertAt(ids[0], "7m", [base])], [
      queryAt(ids[0], "5m", [sample(base, 1)]),
    ]),
    scenario("one isolated failure amid traffic does not fire", [
      requests("success", "0+5x12"), requests("failure", "0 0 0 0 0 1+0x7"),
    ], allQuiet("7m"), [queryAt(ids[0], "7m", [sample(base, 0)])]),
    scenario("error recovery clears a previously firing alert", [
      requests("failure", "0+1x7 7+0x5"),
      requests("success", "0+0x7 20+20x5"),
    ], [alertAt(ids[0], "7m", [base]), alertAt(ids[0], "8m"), alertAt(ids[0], "12m")]),
    scenario("counter reset preserves a sustained failure ratio", [
      requests("success", "0+4x5 0+4x6"), requests("failure", "0+2x5 0+2x6"),
    ], [alertAt(ids[0], "5m", [base]), alertAt(ids[0], "7m", [base]), alertAt(ids[0], "10m", [base])]),
    scenario("no samples stay absent rather than being synthesized healthy", [], allQuiet(),
      ids.map((id) => queryAt(id, "10m", []))),
    scenario("idle observed counters suppress degradation with insufficient evidence", [
      requests("success", "0+0x12"), ...histogram(base, () => 0),
    ], allQuiet(), [queryAt(ids[0], "10m", [sample(base, 0)]), queryAt(ids[1], "10m", [sample(base, 0)])]),
  ];

  const otherInstance = { ...base, instance: "backend-replica:8000" };
  const processor = { ...base, job: "processor", instance: "processor:8001" };
  tests.push(scenario("healthy services instances and operations cannot mask one degraded series", [
    requests("failure", "0+2x12"), requests("success", "0+3x12"),
    requests("success", "0+100x12", otherInstance),
    requests("success", "0+100x12", processor),
    requests("success", "0+100x12", generation),
  ], [alertAt(ids[0], "10m", [base])], [queryAt(ids[0], "10m", [
    sample(base, 1), sample(otherInstance, 0), sample(processor, 0), sample(generation, 0),
  ])]));

  for (const [labels, uid, threshold, previousBucket] of [
    [base, ids[1], 10, 5], [generation, ids[2], 20, 10],
  ]) {
    // 95 of 100 observations in the threshold bucket => interpolated p95 is
    // exactly its upper boundary; 94 of 100 puts p95 in the following bucket.
    const boundary = (le) => le < threshold ? 0 : le === threshold ? 95 : 100;
    const degraded = (le) => le < threshold ? 0 : le === threshold ? 94 : 100;
    tests.push(scenario(`${labels.operation} p95 exactly at threshold is not a breach`, [
      requests("success", "0+100x12", labels), ...histogram(labels, boundary),
    ], allQuiet(), [queryAt(uid, "10m", [sample(labels, 0)])]));
    tests.push(scenario(`${labels.operation} p95 above threshold fires after two minutes`, [
      requests("success", "0+100x12", labels), ...histogram(labels, degraded),
    ], [alertAt(uid, "2m"), alertAt(uid, "3m", [labels]), alertAt(uid, "10m", [labels])], [
      queryAt(uid, "10m", [sample(labels, 1)]),
    ]));
    tests.push(scenario(`${labels.operation} latency is suppressed below minimum volume`, [
      requests("success", "0+0.8x12", labels),
      ...histogram(labels, (le) => degraded(le) * 0.008),
    ], allQuiet(), [queryAt(uid, "10m", [sample(labels, 0)])]));
    tests.push(scenario(`${labels.operation} latency recovers after slow observations leave the window`, [
      requests("success", "0+100x12", labels),
      ...histogram(labels, degraded, (count) => {
        const points = Array.from({ length: 13 }, (_, minute) =>
          minute <= 5 ? count * minute : count * 5);
        return points.join(" ");
      }).map((series, index) => {
        const le = bucketBounds[index] === "+Inf" ? Infinity : bucketBounds[index];
        const points = series.values.split(" ").map(Number);
        // Starting at minute 6 all calls land at or below the previous bucket.
        if (le >= previousBucket) for (let minute = 6; minute <= 12; minute++) points[minute] += 100 * (minute - 5);
        return { ...series, values: points.join(" ") };
      }),
    ], [alertAt(uid, "5m", [labels]), alertAt(uid, "10m"), alertAt(uid, "12m")]));
  }
  return tests;
}
