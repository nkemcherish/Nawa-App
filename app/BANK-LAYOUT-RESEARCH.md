# Nigerian statement layout research — 30 October 2026

## Findings applied

- Kuda's official help supports date-range PDF/Excel statements and Spend Account,
  savings-pocket or combined exports. It does not publish a complete layout specification.
  A publicly indexed historical Kuda PDF was inspected for structure only: day headings,
  time-only rows, Money In/Money Out, category/destination/narration, and running balances.
  Its customer text and financial rows are not shipped as fixtures. That historical
  sample's extracted rows did not reconcile with its printed totals, so it was not
  accepted as a verified import. The observation does not establish its authenticity
  or identify the cause of the mismatch.
- First Bank: published parser code describes separate transaction/value dates,
  references, withdrawal/deposit columns and wrapped details.
- Zenith: published code describes separate debit/credit and value-date columns;
  some totals include brought-forward balances and must not be treated as period flows.
- OPay: published code describes wrapped descriptions around transaction rows,
  separate value dates, Wallet/Savings sections and layouts whose balances do not
  form a simple row chain. No bank-name exception disables NAWA's balance checks.
- PalmPay: published code describes Money In/Money Out with summary totals and no
  running balance column. Such layouts remain on the AI/totals path.
- UBA: published code describes date, description, cheque reference, value date,
  debit, credit and balance. References and value dates must not become transaction amounts.
- Access and Ecobank: public implementations confirm format-specific PDF handling;
  Ecobank variants include amount/reference fields rather than uniform separate columns.
- GTBank: the bank documents PDF and Excel exports. The older public parser's GTBank
  implementation targets Excel, so it is not evidence that a current PDF layout is tested.

## Coverage boundaries

The digital reader recognises actual structural labels instead of a hardcoded list
of bank brands or absolute coordinates. The AI fallback can attempt other layouts;
that is not a claim of bank-specific verification.

| Bank/provider | Evidence reviewed | Current verification status |
| --- | --- | --- |
| Kuda | Official export guide; historical public PDF layout | Fictional grouped-day PDF regressions; affected customer PDF untested |
| First Bank | Public source and redacted PDF sample | Fictional withdrawal/deposit and value-date regressions; sample safely falls back |
| Zenith | Public source and redacted PDF sample | Fictional debit/credit plus value-date regressions; sample safely falls back |
| OPay | Public source and redacted PDF sample | Column context and AI guidance; no claim of live bank certification |
| PalmPay | Public source and redacted PDF sample | AI fallback; no deterministic no-balance reader claimed |
| UBA | Public parser source | Header aliases added; current real PDF untested |
| Access | Public parser source/notebook | Generic labelled-column reader and AI fallback; current real PDF untested |
| Ecobank | Public parser source | AI fallback for single-amount variants; current real PDF untested |
| GTBank | Official export instructions; older Excel parser source | Generic PDF reader and AI fallback; current real PDF untested |
| FCMB, Fidelity, Stanbic IBTC, Sterling, Wema/ALAT, Union, Unity, Polaris, Keystone, Providus, Globus, Moniepoint | Searched; no current authoritative layout fixture validated in this change | Generic reader/AI attempt only; bank-specific coverage unverified |

Public samples with redacted/missing text or inconsistent summaries are not used to
declare successful support. Tests generate fictional PDFs in memory. Multi-account
sections must not be stitched into one continuous ledger; ambiguous combined exports
remain rejected rather than silently dropping savings or bypassing reconciliation.

## Sources

- [Kuda: Get Your Account Statement](https://help.kuda.com/en/articles/8947801-get-your-account-statement)
- [GTBank: How to Generate Your Account Statement](https://gtbank-plc.files.svdcdn.com/production/general/How-to-Generate-Your-Account-Statement.pdf%3Fdm%3D1659029289)
- [bankstract parser implementations](https://github.com/logickoder/bankstract/tree/main/src/bankstract/parsers)
- [ng-bank-parser implementations](https://github.com/devcenter-square/ng-bank-parser/tree/master/lib/ng-bank-parser/parsers)
- [Nigerian bank converter notebooks](https://github.com/tosinshada/bank-statement-converter/tree/main/notebooks)
- [Moniepoint: Account Statement Export Made Easier](https://moniepoint.com/blog/account-statement-export-made-easier) — export choices, not a layout specification
- [Stanbic IBTC Mobile 3.0 FAQs](https://www.stanbicibtcbank.com/static_file/Nigeria/nigeriabank/Personal/Products/Ways%20To%20Bank/Appbility/Stanbic%20IBTC%20Bank%20Mobile%20App%203.0%20FAQs.pdf) — export choices, not a validated statement fixture

External code informed layout research only; NAWA's implementation was written locally.
The public research downloads stay outside the deployment repository.
