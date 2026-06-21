import { HarnessInputError } from "../errors.js";
import { validateManifest } from "../manifest/validate.js";
import { findRepoRoot } from "../repo.js";

async function main(): Promise<void> {
  const inputPath = process.argv.slice(2).find((argument) => argument !== "--");
  if (!inputPath) {
    throw new HarnessInputError("SDD-ARGUMENT", "Usage: validate-manifest <manifest.yaml>");
  }
  const root = await findRepoRoot();
  const report = await validateManifest(root, inputPath);
  process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
  process.exitCode = report.valid ? 0 : 1;
}

main().catch((error: unknown) => {
  const known = error instanceof HarnessInputError;
  const payload = {
    valid: false,
    errors: [
      {
        code: known ? error.code : "SDD-UNEXPECTED",
        instance_path: "/",
        message: error instanceof Error ? error.message : String(error),
      },
    ],
  };
  process.stderr.write(`${JSON.stringify(payload, null, 2)}\n`);
  process.exitCode = 2;
});
