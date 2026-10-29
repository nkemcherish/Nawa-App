# Nawa

## Updated web app and Vercel deployment

The current browser version is in [`app/`](app/). It includes the revised NAWA
interface, dark mode, category details, Gemini PDF reading and categorisation,
and manual report backup/restore. The original Expo application below is preserved.

For Vercel, use **Root Directory: `app`**. Follow
[`DEPLOY-VERCEL.md`](DEPLOY-VERCEL.md) for private server variables and tester access.
No Gemini keys, uploaded bank statements or saved personal reports are included.
The public deployment has not yet been verified. Cloud report sync is not implemented.

**Your money, explained.** Nawa is a local-first statement explainer built with Expo, React Native and TypeScript. The same app runs on Android, iOS and the web.

## Run it

Install Node.js 20 or newer, then from this folder:

```bash
npm install
npx expo start
```

Scan the QR code with Expo Go on iPhone or Android. The first launch needs your computer and phone on the same Wi-Fi network. On Android, scan with Expo Go; on iPhone, scan with the Camera app and open the Expo Go link. You can also press `a` for an Android emulator or `i` for an iOS simulator (macOS required for the iOS simulator).

### Browser preview

```bash
npm run web
```

Open the URL printed by Expo, usually `http://localhost:8081`. To view it on a phone, keep the development server running and connect the phone to the **same Wi-Fi network** as your computer. Find the computer's local IPv4 address, then open `http://YOUR-COMPUTER-IP:8081` on the phone (for example, `http://192.168.1.24:8081`). If the page does not load, allow Node/Expo through the computer's local firewall and confirm the phone is not using mobile data or a guest Wi-Fi network. Expo may print a LAN address you can use directly.

To build a static browser bundle:

```bash
npx expo export --platform web
```

The output is written to `dist/`. Serve that folder with any static file server to share the built preview on your network.

## Main journey

1. Choose **Try demo data** or **Analyse a statement** on Home.
2. For a statement, select a CSV with a header row and either `date`, `description`, `amount` columns or `date`, `description`, `debit`, `credit` columns. The parser accepts quoted CSV fields, ISO dates, and common day/month/year dates. Rows it cannot validate are skipped with an explanation.
3. Review the transactions. Tap a row to change its type or category. Ambiguous items are marked **Needs review** and left out of all totals until corrected.
4. Open the report, then save it to the device. Find it in **Reports**, reopen it, compare saved periods, or delete it after confirmation.

Example CSV:

```csv
date,description,amount
2026-08-01,Salary,485000
2026-08-02,"Shoprite, Lekki",-38250
2026-08-05,Transfer to savings,-50000
2026-08-16,Jumia order refund,8900
```

## Money definitions

- **Income:** values from a CSV credit column, or rows clearly identified as salary/payroll/interest income.
- **Spending:** purchases and bills. Transfer-like or unknown rows are flagged for review instead of being guessed as spending.
- **Transfers:** counted separately and excluded from spending and the remaining calculation until the user classifies an ambiguous row.
- **Refunds:** shown separately and added back when calculating remaining money.
- **Remaining:** income minus spending plus refunds. It is not a bank balance; opening and closing balances are not currently reconciled.

All values are parsed from transactions and calculated in deterministic TypeScript. For amount-only CSVs, negative values are treated as outflows; positive unsigned values are assigned only when a description clearly identifies income, a refund, or a known merchant. Other ambiguous rows are flagged for review. Naira display uses `en-NG` formatting. Demo transactions are synthetic.

## Privacy and storage

Nawa does not connect to a bank or send statements to a service. CSV content is read on-device for parsing; the original is not retained by the app. Saved reports and edited transaction classifications are stored in AsyncStorage on the device under a versioned key. Use **Settings → Delete all local data** to remove all saved reports. No analytics, external financial-data upload, AI calls, or Gemini integration are included.

## Supported files and current limitations

- **CSV:** parsed and validated on-device. Supported headers are `date`/`transaction date`/`posted date`, `description`/`details`/`narration`/`merchant`/`transaction`, `amount`/`value`, or `debit` and `credit`.
- **PDF:** not supported in this version. Bank PDF layouts vary, and no local extractor has been tested reliably across Expo Web, iOS and Android. Nawa tells you to export CSV; it does not pretend to read the PDF.
- **XLS/XLSX, encrypted files, opening/closing balance reconciliation, bank-specific layouts:** not supported yet.
- Duplicate rows are skipped within an import when date, description and amount match. Category suggestions are intentionally conservative; unmatched descriptions need your review.

## Checks

```bash
npm test
npm run typecheck
npx expo export --platform web
```

The tests cover totals and definitions, category aggregation, conservative transaction classification, CSV quoting, debit/credit columns, duplicates, malformed rows, signed income, refunds, and empty files.

## Project structure

- `App.tsx` — connected mobile-first app screens and interactions
- `src/domain/` — transaction types, demo data and deterministic financial calculations
- `src/services/` — local CSV parsing and report persistence
- `tests/` — calculation, CSV parser and local report-storage unit tests
- `assets/nawa-logo.svg` and `NAWA_BRAND_GUIDE.md` — supplied Nawa brand assets
