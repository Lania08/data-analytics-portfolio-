-- Q1. Average turnaround by specialty (decided applications only). Answers: which specialties wait the longest from application to decision?
SELECT specialty, COUNT(*) AS decided_apps, ROUND(AVG(CAST(total_days_received_to_decision AS INTEGER)), 1) AS avg_days, MIN(CAST(total_days_received_to_decision AS INTEGER)) AS fastest_days, MAX(CAST(total_days_received_to_decision AS INTEGER)) AS slowest_days FROM applications WHERE status IN ('Approved', 'Denied', 'Withdrawn') AND total_days_received_to_decision <> '' GROUP BY specialty ORDER BY avg_days DESC;

-- Q2. Bottleneck steps. Answers: where do applications get stuck in the workflow?
SELECT step_name, COUNT(*) AS step_completions, ROUND(AVG(CAST(days_in_step AS INTEGER)), 1) AS avg_days_in_step, MAX(CAST(days_in_step AS INTEGER)) AS worst_days FROM application_steps WHERE exited_date <> '' GROUP BY step_name ORDER BY avg_days_in_step DESC;

-- Q3. Applications stuck right now (open, 30+ days in current step). Answers: what needs a coordinator's attention today?
SELECT application_id, provider_name, specialty, current_step, days_in_current_step, received_date FROM applications WHERE status IN ('In Progress', 'On Hold') AND CAST(days_in_current_step AS INTEGER) > 30 ORDER BY CAST(days_in_current_step AS INTEGER) DESC;

-- Q4. Aging buckets for the open queue. Answers: how old is the work still sitting open?
SELECT CASE WHEN julianday('2026-10-03') - julianday(received_date) <= 30 THEN '0-30 days' WHEN julianday('2026-10-03') - julianday(received_date) <= 60 THEN '31-60 days' WHEN julianday('2026-10-03') - julianday(received_date) <= 90 THEN '61-90 days' ELSE '90+ days' END AS aging_bucket, COUNT(*) AS open_apps FROM applications WHERE status IN ('In Progress', 'On Hold') GROUP BY aging_bucket ORDER BY aging_bucket;

-- Q5. Monthly volume: received vs decided. Answers: is the team keeping up with incoming applications?
WITH months AS (SELECT strftime('%Y-%m', received_date) AS m FROM applications UNION SELECT strftime('%Y-%m', decision_date) FROM applications WHERE decision_date <> '') SELECT m AS month, (SELECT COUNT(*) FROM applications WHERE strftime('%Y-%m', received_date) = m) AS received, (SELECT COUNT(*) FROM applications WHERE strftime('%Y-%m', decision_date) = m) AS decided FROM months ORDER BY month;

-- Q6. Slowest primary-source verification items. Answers: which verifications drag the longest?
SELECT verification_item, COUNT(*) AS items_requested, ROUND(AVG(CASE WHEN days_to_return <> '' THEN CAST(days_to_return AS INTEGER) END), 1) AS avg_days_to_return, SUM(CASE WHEN returned_date = '' THEN 1 ELSE 0 END) AS still_pending FROM verification_items GROUP BY verification_item ORDER BY avg_days_to_return DESC;

-- Q7. Decision outcomes by specialty. Answers: do some specialties get denied more often?
SELECT specialty, COUNT(*) AS decided_apps, SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) AS approved, ROUND(100.0 * SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) / COUNT(*), 1) AS approval_rate_pct FROM applications WHERE status IN ('Approved', 'Denied', 'Withdrawn') GROUP BY specialty ORDER BY approval_rate_pct;
