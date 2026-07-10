# Daily & Periodic Checklists

## 1. Start-of-Shift Checklist
To be completed by the incoming operator within the first 15 minutes of their shift.

- [ ] Log into the HMI with personal credentials (Do not share logins).
- [ ] Verify the total number of Active Alarms matches the handover notes from the previous shift.
- [ ] Check the **System Health** panel (Ensure all core services show as `GREEN`).
- [ ] Review the **AI Insights** panel for any slow-developing anomalies.

## 2. End-of-Shift Checklist
To be completed by the outgoing operator.

- [ ] Ensure all alarms have been acknowledged and appropriate comments entered.
- [ ] Export the "Shift Summary Report" from the Historian.
- [ ] Log out of the HMI workstation.

## 3. Weekly Verification
To be completed by the Shift Supervisor every Sunday.

- [ ] Verify that the automated Historian Database backups occurred successfully.
- [ ] Run a test query on the Historian covering the entire 7-day period.
- [ ] Review the `AuditLogger` for any failed login attempts or unauthorized access.

## 4. Pre-Deployment Review
To be completed by Engineering before pushing new code to Production.

- [ ] Validate the `APP_ENV` variable is correctly set to `production`.
- [ ] Ensure no `[SIMULATION ONLY]` drivers are active in the `SystemConfig`.
- [ ] Confirm all tests pass on the Staging environment.
