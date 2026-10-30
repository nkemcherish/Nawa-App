# PDF reader coverage

The configured statement pipeline first attempts source-labelled digital PDF
tables. Header positions identify debit/credit, withdrawal/deposit or money-in/out
columns, including reordered columns and separate value dates. A local result is
used only with readable transaction balances, printed opening/closing balances,
and successful reconciliation. Ambiguous layouts and scanned pages use Gemini.
Neither path persists uploaded PDFs.

The shared header reader combines headings split across two visual lines, recognises
transaction particulars/narrative aliases and carries a printed date into complete
subsequent money rows with blank date cells. Layout research is applied through
structural signatures, not bank-name mentions: Kuda grouped-day guidance, First Bank
withdrawal/deposit guidance and separate value-date guidance share the same pipeline.
OPay-style wallet tables now have a direct reader: descriptions are assigned to
the nearest transaction baseline, including continuation pages without headers.
It requires both printed debit/credit counts, both totals and opening/closing
balances. A direct extraction whose counts, totals and opening/closing reconcile
may return with an explicit visible warning when printed running balances do
not chain. This exception is unavailable to AI extractions. Missing counts,
incorrect totals, ambiguous descriptions and separate savings sections fall back.

30 October regression: a permissioned six-page OPay statement was read locally
as 103 transactions; both source counts, debit/credit totals and opening/closing
balances matched. Individual running balances did not all chain and are disclosed
as unverified. No customer PDF, names or transaction contents are committed.

Gemini processes pages in groups of four, with statement-period, preceding day
heading and source column-position context carried into each group. This matters
for Kuda-style grouped dates and continuation pages without repeated headings.
Validation feedback guides a bounded reread. Cross-group mismatches reread the
implicated groups once; persistent failures block the report.

Reconciliation checks printed debit/credit totals, printed transaction counts,
opening/closing balances, and consecutive running balances in either date order.
For statements longer than four pages, statement-wide summary totals are not checked
against individual chunks. Recognised first-page printed summaries are read directly
from PDF text positions and checked against the complete extraction instead. Running
balances are also checked across chunk boundaries. Other summary fields are transcribed
by AI and are not an independent second extraction.

Live checks on 29 October 2026:
- Fictional digital PDF: debit and credit extracted; categorisation fell back to
  review on one service failure, without losing extracted transactions.
- Fictional scanned image-only PDF: both transactions extracted; opening/closing
  balance, running balances, debit/credit totals and transaction count matched.

Automated tests cover malformed amounts, impossible dates, incomplete output,
missing rows, foreign currencies, reversed order, inconsistent balances,
encrypted/damaged PDFs, duplicate preservation and multi-chunk processing. Fictional
PDF fixtures also cover column-order variants, withdrawal/deposit labels, value dates,
Kuda-style grouped days across pages, source context passed to AI, direct summary
checks on long PDFs, local success without AI and safe fallback after local failure.

Research and coverage status: [BANK-LAYOUT-RESEARCH.md](BANK-LAYOUT-RESEARCH.md).
Fictional format tests are not certification of every bank's current statement export.

Limits: 12 MB, 65 pages, NGN only, password-protected files need an unlocked copy.
No guarantee of every bank layout or every damaged/blurred document. Missing
reconciliation fields are disclosed rather than treated as verified. Real bank
fixtures remain needed before claiming bank-specific accuracy or production readiness.

Shared categorisation regression fix: local PDFs and CSV imports send unresolved debit transfers through purpose classification with full narration/recipient text. Responses require source-substring evidence and high confidence. Description text is preserved without the old 240-character truncation, including backups. All merchant groups are processed in batches rather than silently stopping at 100. AI extraction also explicitly preserves recipient/destination columns. Live provider category decisions are not guaranteed by mocked tests.

Sectioned-account regression (30 October): a permissioned 59-page statement now reads locally as 936 transactions across five independently reconciled sections. Source totals and opening/closing match in every section; nonsequential running balances are explicitly warned. Recipient and narration fields are preserved, source savings movements are excluded from spending, and explicit food notes (groceries, popcorn, shawarma, food and water) categorise directly. Right-aligned balance boundaries are inferred from printed money positions. Tests use fictional sections only; no customer data is committed.
