# Publish NAWA for friend testing

Deployment files are prepared but no public deployment has been made or verified.

1. Push this project to your GitHub repository. Do not add keys or .env files.
2. In Vercel choose Add New → Project, then import that repository.
3. Set Root Directory to `app`, Framework to Other. `vercel.json` supplies the
   build command and output folder. The Python API is `api/parse.py`.
4. Add server environment variables for Preview and Production:
   - `GEMINI_API_KEY`: your new private Gemini key.
   - `GEMINI_MODEL`: `gemini-3.1-flash-lite`.

5. Deploy a preview. Test onboarding, themes, a synthetic PDF, 
   invalid PDF, manual backup and report/category navigation before sharing.
6. Promote the verified deployment to Production. Share the production URL.
   Future Git pushes deploy updates at the same project URL.

## Current testing limits

- Public API accepts up to 4 MB per upload (local testing still accepts 12 MB).
- Function timeout is 300 seconds. Large statements or repeated AI retries can
  exceed this. A queued job pipeline and direct private storage uploads are needed
  for larger documents/longer jobs.
- Visitors upload without a shared password. Per-user rate limiting is not yet
  implemented. Monitor Gemini quotas before wider public release.
- Report storage remains in each browser, with manual download/import backup.
  Cloud sync and automatic backups are not implemented.
- Free-tier Gemini processing terms still apply. Use synthetic/redacted data for
  early testing; the privacy details remain accessible in the interface.
- No raw statements are deliberately written to disk by the API. Deployment
  verification is still required; a successful local build is not a successful deploy.

References: https://vercel.com/docs/git,
https://vercel.com/docs/environment-variables,
https://vercel.com/docs/functions/limitations

