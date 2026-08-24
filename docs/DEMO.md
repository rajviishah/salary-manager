# Demo script (~2–3 minutes)

1. **Open the deployed URL** (or `http://localhost:8000` after `docker compose up --build`). Wait if it is a first boot or a Render wake-up; Dashboard should show USD-normalized headcount and payroll, not an empty shell.

2. **Dashboard.** Point at summary cards (headcount, total/avg/median/p90 USD). Scroll to country / department / level tables or charts. Toggle Active vs Inactive to show the filter is server-side.

3. **Employees.** Open Employees. Search `EMP00001` or filter country + department. Change page to show pagination (25 rows, not 10k).

4. **Edit salary.** Open one row → change amount or currency → save. Back to Dashboard (refresh if needed) and note totals moved. Mention there is no login and Render SQLite is not durable.
