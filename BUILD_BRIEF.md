# NAWA: COMPLETE MOBILE APP BUILD PROMPT FOR CLAUDE

You are the lead product designer and senior mobile engineer. Build the **entire Nawa app in one complete implementation**, not a series of mockups or five disconnected code screens. Do not stop after the first screen, do not return only snippets, and do not ask me to approve each screen before continuing. Finish the complete app, run it, test it, and then hand it over for review. **Do not integrate Gemini AI yet.** I will review the complete app first and give you a separate Gemini integration prompt later.

## 1. Product and outcome

**Product:** Nawa  
**Tagline:** Your money, explained.

Nawa helps people understand where their money went by analysing bank statements and turning transactions into a clear, human explanation. It should answer: “Where did my money go?” It is not a generic budgeting dashboard and should not require users to manually log every expense.

Build a real, usable, mobile-first app for **Android and iOS**, using **Expo + React Native + TypeScript**. If Expo web is practical, enable it as a useful browser preview too, but do not sacrifice the native mobile experience. Use a project structure that can be opened and run locally. Prefer free and open-source dependencies. Do not require a paid service, paid API, bank login, BVN, or bank connection.

## 2. Non-negotiable build rules

- Implement the whole app in this run: all screens, navigation, state, data models, calculations, persistence, empty states, loading states, error states, and interactions.
- Do not deliver static screens with fake buttons. Every visible control must work or be clearly marked as unavailable.
- Do not simulate a successful upload while ignoring the file. Never tell the user a statement was analysed unless its contents were actually parsed and validated.
- Include a clearly labelled **Try demo data** path so the app can be explored without a real statement.
- Do not integrate Gemini or any other generative AI in this phase. No AI API keys, calls, SDKs, hidden network requests, or AI-generated calculations.
- Keep financial calculations deterministic and testable in normal code. Never ask an LLM to calculate totals.
- Process statements on-device where feasible. Do not send statements or transactions to a third-party service. If full local PDF extraction is not supported on a target platform, explain the limitation in the UI and offer a usable CSV route or demo data. Do not silently upload the file.
- Do not use real personal banking information in sample data. Create synthetic Nigerian-style demo transactions.
- Never collect BVN, bank passwords, PINs, OTPs, or online-banking credentials.
- Build the complete implementation before handing it over. You may make sensible design decisions without asking me questions. Document genuine limitations instead of hiding them.
- Preserve the supplied logo and brand guide in this project pack. Use the provided SVG logo asset rather than inventing a different logo. If you improve it, keep the same basic concept and update the asset file.
- Do not leave `TODO`, placeholder screens, non-functional controls, or unexplained hard-coded demo totals in the final build.
- Keep code maintainable and separate UI, parsing, calculations, storage, and types.

## 3. Brand direction

Use the included `NAWA_BRAND_GUIDE.md` and `assets/nawa-logo.svg`.

- Forest green: `#173D32`
- Warm paper: `#F7F4EC`
- Sage: `#C7DB9A`
- Ink: `#292D29`
- Mist: `#E7E4DC`
- Headlines: DM Serif Display, or a visually similar available serif if custom font setup is not practical.
- UI/body: Inter, or a clean system sans-serif fallback.
- Mood: editorial, calm, trustworthy, warm, clear, and human.
- Use a restrained layout, clear hierarchy, generous breathing room, and moderate 12–16 px corner radii.
- Avoid generic fintech styling: no neon gradients, excessive glassmorphism, piles of cards, overdecorated charts, or a dashboard full of tiny metrics.
- Use accessible contrast, readable type, clear touch targets, and sensible keyboard/screen-reader labels.
- Mobile layout is the priority. Design for small phones first, then larger phones and tablets. Respect safe areas and avoid clipped content.
- Use the same design system consistently across every screen. Do not redesign the brand halfway through.

## 4. Required app structure and screens

Build these connected flows, not isolated screens:

### A. Home
- Welcome/title and short explanation of what Nawa does.
- Primary action: **Analyse a statement**.
- Secondary action: **Try demo data**.
- Show the most recent saved report when one exists.
- A simple summary of the latest period only when real or demo data exists.
- Helpful empty state for a first-time user.
- Short, honest privacy note: statement files are processed locally where supported and are not sent to an AI service in this phase.

### B. Statement import
- Allow selecting a statement file using the platform's native document picker.
- Support CSV first, then text-based PDF where reliable local extraction is supported. Clearly explain accepted formats and limitations before import.
- Validate file type, size, empty files, malformed data, and unsupported PDF formats.
- Show a progress/loading state during parsing.
- Never show success unless the file was genuinely read and parsed.
- Keep the original file on-device only as needed for parsing; do not retain it unnecessarily.
- Offer demo data if a file cannot be parsed.
- Do not use a fake upload animation as a substitute for parsing.

### C. Transaction review
- Show imported transactions with date, description, amount, transaction direction, and category.
- Support search, date/period filtering, and category filtering.
- Allow the user to change a category and mark a transaction as income, expense, transfer, refund, or needs review.
- Include a clear way to correct ambiguous transactions.
- Distinguish transfers between a user's own accounts from actual spending where possible. If the parser cannot confidently tell, mark the transaction **Needs review** rather than inventing certainty.
- Reflect edits in the report immediately.
- Add useful empty, error, and no-results states.

### D. Money report
- Explain the selected period in plain language.
- Show verified income, actual spending, outgoing transfers, refunds, and net remaining separately. Do not count transfers as spending by default.
- Provide category breakdown and a transaction list that lets users drill down.
- Include a small number of useful observations generated with deterministic rules, for example: largest spending category, highest-spend day, or change compared with a previous saved period. Only show an observation when the underlying data supports it.
- Explain the difference between spending, transfers, refunds, and income in a simple help area.
- Include a date/period selector and a route back to transaction review.
- Use currency formatting for Nigerian naira (₦) and avoid misleading totals.
- If opening/closing balances are available, reconcile them where possible. If totals do not reconcile, show a clear warning and do not pretend the data is verified.

### E. Saved reports
- Save a report locally with period, creation date, source file label (not the file's contents), transactions, category edits, and computed totals.
- Persist saved reports after the app closes and reopens.
- Allow opening, renaming if sensible, comparing two periods, and deleting a saved report with confirmation.
- Do not lose previous reports when a new statement is imported.
- Make it clear when a report is based on demo data.
- Include empty and error states.

### F. Settings / help
- Include a small settings/help area with privacy explanation, supported-file guidance, category definitions, app version, and a way to clear local data with a confirmation step.
- No login or account creation is needed for this first version.
- Do not add unnecessary screens just to make the app feel bigger.

## 5. Financial data and calculation rules

Implement and unit-test a single source of truth for calculations.

Each transaction should have a stable ID, date, description, signed amount or amount plus direction, type, category, and review status. Use a consistent typed model.

- Keep income separate from expenses.
- Keep transfers separate from spending.
- Keep refunds separate and apply them consistently. State whether the report shows gross spending and refunds separately or net spending, and never mix definitions silently.
- Do not count an incoming transfer as earned income unless the user confirms it.
- Do not count a transfer between own accounts as spending.
- Handle debit/credit columns and signed amounts correctly.
- Handle duplicate rows, dates, commas in descriptions, negative amounts, missing values, and different date formats safely.
- Never infer a category with unjustified certainty. Include `Needs review` as a valid state.
- Document the exact definitions used in the UI.
- If the statement includes opening and closing balances, compare the expected balance movement with parsed transactions when the statement format permits it. Surface a mismatch.
- Use Nigerian naira in all demo examples and formatting.
- Use synthetic demo data that includes income, everyday expenses, a transfer, a refund, and at least one ambiguous item to review. Ensure the totals shown are calculated from the same demo transactions, not separately hard-coded.
- Add automated tests for totals, refunds, transfers, date ranges, edits, duplicates, and reconciliation where possible.

## 6. Parsing architecture

Build a parser layer independent of the UI, with a clear interface such as `parseStatement(file) -> parsed transactions + metadata + warnings`.

- CSV parsing must be real and reliable, not based on splitting each line on commas. Use a suitable open-source CSV parser.
- For PDF, use a compatible local extraction approach only after checking that it works in the chosen Expo targets. Do not claim universal support for every Nigerian bank.
- Add parser adapters or configuration for known formats only when you can implement and test them.
- If considering an existing open-source Nigerian statement parser, inspect its maintenance, licence, dependencies, supported banks, and whether it requires a hosted API. Prefer a local/self-hosted engine with a compatible licence. Do not send statements to a third-party parser API in this phase.
- Show the detected bank/format only if confidently identified.
- If extraction is incomplete or the layout is unsupported, show a clear explanation and let the user use CSV or demo data.
- Include synthetic test fixtures for each supported format and document what was tested.
- Do not make up transactions from unreadable PDF content.

## 7. Persistence and privacy

- Persist reports and user category corrections locally using an Expo-compatible storage solution.
- Keep a versioned local data model and handle corrupt/missing saved data gracefully.
- Do not retain uploaded originals unless necessary.
- No analytics SDK, advertising SDK, remote database, external upload endpoint, or AI API in this phase.
- Provide a clear local-data deletion flow.
- Document what data is stored and where.
- If any library requires network access for a non-essential feature, explain it and avoid it if possible.

## 8. Navigation and interaction

Use a clear, mobile-appropriate navigation pattern, such as bottom tabs for Home, Reports, and Settings plus stack navigation for import, review, and report detail. Avoid excessive tabs.

The core journey must work end-to-end:

1. Open the app.
2. Choose demo data or import a statement.
3. Parse/validate the statement.
4. Review and correct transactions.
5. View the report and explanations.
6. Save the report.
7. Close/reopen the app.
8. Open the saved report and compare it with another period.
9. Delete a saved report or clear local data after confirmation.

Use consistent back navigation and prevent accidental data loss. Show confirmation before destructive actions.

## 9. Technical requirements

- Use Expo + React Native + TypeScript.
- Use a stable Expo-supported navigation approach.
- Use a sensible folder structure, for example `app/`, `components/`, `features/`, `services/`, `lib/`, `types/`, `assets/`, and `tests/`.
- Use a consistent lint/format setup if practical.
- Add unit tests for financial calculations and parser utilities.
- Include `.env.example` only if needed. Do not put secrets in source code.
- Include a complete `README.md` with beginner-friendly setup instructions for Windows, macOS, and Linux.
- Explain how to run the app in Expo Go if compatible, and how to run a browser preview if web is enabled.
- Explain what requires a real device versus a simulator.
- Include a list of exact commands, not vague instructions.
- Do not say that you ran a command or test unless you actually ran it and saw the result.

## 10. Acceptance checklist

Before handing over, check every item and report pass/fail honestly:

- [ ] All required screens are implemented and connected.
- [ ] No placeholder screen or dead button remains.
- [ ] The app launches successfully.
- [ ] Demo journey works from Home through Review, Report, Save, and Saved Reports.
- [ ] CSV import is actually parsed and validated.
- [ ] PDF import is either genuinely supported and tested on the target, or its limitation is explained honestly.
- [ ] Totals update after category/type edits.
- [ ] Transfers are not silently counted as expenses.
- [ ] Refunds are shown consistently.
- [ ] Reports persist after restart.
- [ ] Compare and delete flows work.
- [ ] Data clearing requires confirmation.
- [ ] Tests for financial calculations pass.
- [ ] Layout is usable on small mobile screens.
- [ ] Logo and brand guide are used.
- [ ] No Gemini/AI integration or third-party financial-data upload exists.
- [ ] README explains setup, usage, limitations, and troubleshooting.

## 11. Deliverables

Create a complete project folder called `nawa-app` containing all source code, assets, tests, and documentation. Use the supplied `assets/nawa-logo.svg` and brand guide from this pack. Do not merely describe the files; create them in the workspace.

At the end:
1. Run the app and all relevant tests/build checks that are available in your environment.
2. Fix errors you find rather than just listing them.
3. Give me the exact project folder path.
4. Give me the exact beginner-friendly commands to install dependencies and run it.
5. Summarise the screens and core flows that work.
6. List any limitations honestly, especially bank statement formats that are not yet supported.
7. State clearly that Gemini has not been integrated yet.
8. Provide a short review checklist for me to use before I approve the Gemini phase.

**Now build the complete app in one pass. Do not stop after planning or after creating a few screens.**
