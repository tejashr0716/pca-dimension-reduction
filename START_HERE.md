# Start here

1. Read `README.md` and run the project locally.
2. Click **Try the 100-feature sample**: this calls the real analysis API.
3. Check the preprocessing audit; 2,000 input rows are not 2,000 fitted rows.
4. Run `python -m pytest -q` and `python scripts/benchmark.py`.
5. Work through `docs/INTERVIEW_GUIDE.md`, including the hands-on experiments.
6. Follow `docs/DEPLOYMENT.md` to replace the GitHub project safely and deploy.

The code is a complete replacement package, not a patch or a snippet.
The original synthetic sample and its generation recipe are preserved.
The UI computes its metrics from the API; it does not insert a preset 99.7%.

The rebuilt code is published in this repository. A working public app requires
Python hosting; its verified link will be listed in `README.md` after deployment.
The original project is preserved on `backup/pre-pca-rebuild-2026-09-30`.

For interview preparation, start with the 45-second explanation, trace one
request through the source, and demonstrate one failure case yourself.
