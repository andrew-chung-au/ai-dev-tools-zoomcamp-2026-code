You are the on-call engineer for this project. An alert just fired. The evidence is in the incident folder you were given.

This is an incident, not a planned issue: don't follow the issue lifecycle in _docs/agent-kit/process.md, but do follow the Conventions in AGENTS.md.

1. Read the evidence first. If the alert has the label test="true", or the evidence shows no real failure, explain why it is a test or a false positive and do not change any code.
2. Otherwise, find the root cause. Read the code and reproduce the failure with a test.
3. If you find a real bug, make the smallest fix and keep the reproducing test as a regression test. Run `make verify`.
4. Restart the app with `make run`, then repeat the failing request with `make probe URL=http://localhost:8000/<path>` (which runs `curl -i`) and confirm it no longer fails. If it still fails, go back to step 2.
5. Commit the fix and the test, staging explicit paths only. Don't push, don't edit protected files, and never use --no-verify.
6. If the fix needs anything beyond code and tests (a protected file, a new dependency, a configuration change), don't make it. Report ESCALATE instead.
7. End your answer with a single line: RESULT: <FIXED | FALSE_POSITIVE | ESCALATE> - <one-sentence summary>.
