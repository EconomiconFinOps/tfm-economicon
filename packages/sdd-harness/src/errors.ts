export class HarnessInputError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "HarnessInputError";
    this.code = code;
  }
}

export class HarnessBlockedError extends Error {
  readonly issues: import("./types.js").ValidationIssue[];

  constructor(message: string, issues: import("./types.js").ValidationIssue[]) {
    super(message);
    this.name = "HarnessBlockedError";
    this.issues = issues;
  }
}
