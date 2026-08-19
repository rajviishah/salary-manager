# ACME Salary Manager — Product Requirements

## Goal

Build a web application that lets ACME’s HR Manager manage current salary data for about 10,000 employees across multiple countries, and answer: how does this organization pay people? The product replaces Excel with a searchable directory, validated salary updates, and a pay-insights dashboard backed by server-side aggregations.

## Users

Primary persona: HR Manager of ACME. The app models a single operator who maintains employee records, updates current compensation, and reviews pay distribution. No other roles are modeled.

## Problem

Salary data lives in Excel. At 10,000 employees across countries, currencies, departments, and job levels, the workbook is slow to search, easy to corrupt, and weak at comparative questions (median pay by country, currency mix, p90 by job level). HR needs a web tool to find people quickly, keep current salary accurate, add new hires with a starting salary, and see organization-wide pay patterns without exporting to another spreadsheet.

## In scope

**Employee directory.** Paginated list. Search by name, email, or employee ID. Filter by country, department, job level, and employment status. Sort so HR can work the full population without loading every row at once.

**Employee detail.** View and edit profile fields needed for pay context (identity, location, org placement, status). Update *current* salary: amount, currency, and effective date, with validation (positive amount, known currency, coherent effective date).

**Add employee.** Create a new employee together with a starting salary so the system is not seed-only.

**Pay insights dashboard.** Headcount; total and median payroll plus p50–p90 in USD-normalized terms; breakdowns by country, department, and job level; currency mix. Aggregations run in SQL on the server, not in the browser. Conversion uses a small seeded FX table.

**Seed data.** Deterministic seed of 10,000 realistic employees across multiple countries and currencies, plus a small FX table for USD comparison and tests.

**Tests.** FastAPI unit and API tests for core rules: salary validation, create/update flows, and insight aggregations.

## Out of scope (and why)

* **Auth, SSO, and RBAC.** One persona, demo-first. Identity and permissions would dominate the build without changing the salary-management problem.
* **Payroll processing.** Tax, net pay, pay runs, benefits, equity, and bonuses are compensation *operations*, not current-salary *records*. Including them would turn this into a payroll engine.
* **Merit cycles, approvals, and audit log.** Real HR needs, but they require workflows and history this assessment does not ask for. The product tracks current salary, not a cycle.
* **Excel/CSV import.** Migration tooling would recreate the spreadsheet problem. The brief is to leave Excel; seed data stands in for the one-time load.
* **Postgres, Redis, and microservices.** Ten thousand rows are well within SQLite. Extra infrastructure adds ops cost without product value here.

## Success criteria

* HR can search, filter, and page through 10,000 employees with acceptable interactive latency.
* HR can add an employee with a starting salary and update current salary, with validation enforced server-side.
* The dashboard reports USD-normalized headcount, total/median/percentile payroll, and breakdowns that match SQL aggregations on seeded and subsequently edited data.
* Core API rules are covered by automated FastAPI tests.
* This requirements document is the first commit; application code follows it.

## Key assumptions

* Stack: FastAPI backend; React with Vite and TypeScript frontend; SQLite. UI: Ant Design, Recharts, and TanStack Query.
* "Current salary" is a single active compensation record per employee (amount, currency, effective date), not a full historical ledger.
* FX conversion looks up the seeded table; rates are static for the demo.
* Employment status is a simple filterable field (for example active vs inactive); there is no lifecycle workflow.
* Local/demo deployment: no production hardening, multi-tenancy, or high availability.
* Ten thousand employees is the target scale for seed, queries, and pagination not a claim of unbounded growth.

