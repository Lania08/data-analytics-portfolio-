/* ============================================================================
   Provider roster data-quality analysis — SYNTHETIC data
   ----------------------------------------------------------------------------
   Question: "Which providers in a credentialing roster have the worst
              data-quality issues, and where should cleanup start?"

   Run against the roster with sqlite3, e.g.:

       sqlite3 :memory: \
         -cmd ".mode table" \
         ".import --csv --skip 1 providers_synthetic.csv providers" \
         < analysis.sql

   (Or load the CSV into a table named `providers` first, then paste any
   query below.)  The reference date '2026-10-03' is the "today" the demo
   data was generated against; change it if you re-run on a later date.
   ============================================================================ */

-- Q1. Missing or malformed NPIs (must be 10 digits; real NPIs start 1-4)
SELECT row_id, provider_name, specialty, state, npi AS npi_value
FROM providers
WHERE npi IS NULL
   OR trim(npi) = ''
   OR length(trim(npi)) <> 10
   OR trim(npi) GLOB '*[^0-9]*'
ORDER BY row_id;

-- Q2. Duplicate NPIs (same NPI on more than one record)
SELECT npi,
       COUNT(*) AS record_count,
       group_concat(row_id, ', ') AS row_ids,
       group_concat(provider_name, ' | ') AS names
FROM providers
WHERE trim(npi) <> ''
GROUP BY npi
HAVING COUNT(*) > 1;

-- Q3. Providers whose license is already EXPIRED (as of 2026-10-03)
SELECT row_id, provider_name, specialty, state,
       license_number, license_expiry_date,
       CAST(julianday('2026-10-03') - julianday(license_expiry_date) AS INTEGER)
           AS days_expired
FROM providers
WHERE date(license_expiry_date) IS NOT NULL
  AND date(license_expiry_date) < date('2026-10-03')
ORDER BY license_expiry_date;

-- Q4. Licenses expiring in the NEXT 90 days (cleanup queue)
SELECT row_id, provider_name, specialty, state,
       license_number, license_expiry_date,
       CAST(julianday(license_expiry_date) - julianday('2026-10-03') AS INTEGER)
           AS days_until_expiry
FROM providers
WHERE date(license_expiry_date) IS NOT NULL
  AND date(license_expiry_date) BETWEEN date('2026-10-03') AND date('2026-10-03', '+90 days')
ORDER BY license_expiry_date;

-- Q5. Prescribers with EXPIRED DEA registrations
SELECT row_id, provider_name, specialty, state, dea_expiry_date,
       CAST(julianday('2026-10-03') - julianday(dea_expiry_date) AS INTEGER)
           AS days_expired
FROM providers
WHERE prescribes_flag = 'Y'
  AND date(dea_expiry_date) IS NOT NULL
  AND date(dea_expiry_date) < date('2026-10-03')
ORDER BY dea_expiry_date;

-- Q6. Prescribers with NO DEA date on file at all
SELECT row_id, provider_name, specialty, state
FROM providers
WHERE prescribes_flag = 'Y'
  AND (dea_expiry_date IS NULL OR trim(dea_expiry_date) = '')
ORDER BY row_id;

-- Q7. Stale CAQH attestations (payers require re-attestation every 120 days)
SELECT row_id, provider_name, specialty, state, caqh_attestation_date,
       CAST(julianday('2026-10-03') - julianday(caqh_attestation_date) AS INTEGER)
           AS days_since_attestation
FROM providers
WHERE date(caqh_attestation_date) IS NOT NULL
  AND date(caqh_attestation_date) < date('2026-10-03', '-120 days')
ORDER BY caqh_attestation_date;

-- Q8. Missing CAQH attestation date
SELECT row_id, provider_name, specialty, state
FROM providers
WHERE caqh_attestation_date IS NULL OR trim(caqh_attestation_date) = ''
ORDER BY row_id;

-- Q9. Board certification not in good standing
SELECT row_id, provider_name, specialty, state, board_certification_status
FROM providers
WHERE board_certification_status IN ('Lapsed', 'Not Certified')
ORDER BY board_certification_status, row_id;

-- Q10. Malformed / unparseable dates anywhere in the roster
SELECT row_id, provider_name, 'license_expiry_date' AS field,
       license_expiry_date AS bad_value
FROM providers
WHERE trim(license_expiry_date) <> '' AND date(license_expiry_date) IS NULL
UNION ALL
SELECT row_id, provider_name, 'dea_expiry_date', dea_expiry_date
FROM providers
WHERE trim(dea_expiry_date) <> '' AND date(dea_expiry_date) IS NULL
UNION ALL
SELECT row_id, provider_name, 'caqh_attestation_date', caqh_attestation_date
FROM providers
WHERE trim(caqh_attestation_date) <> '' AND date(caqh_attestation_date) IS NULL
ORDER BY row_id, field;

-- Q11. Issue rate by specialty: providers with at least one data-quality flag
WITH flags AS (
    SELECT row_id, specialty,
           CASE WHEN npi IS NULL OR trim(npi) = ''
                     OR length(trim(npi)) <> 10
                     OR trim(npi) GLOB '*[^0-9]*'
                THEN 1 ELSE 0 END AS bad_npi,
           CASE WHEN trim(license_number) = '' OR license_number IS NULL
                THEN 1 ELSE 0 END AS missing_license_no,
           CASE WHEN date(license_expiry_date) IS NOT NULL
                     AND date(license_expiry_date) < date('2026-10-03')
                THEN 1 ELSE 0 END AS expired_license,
           CASE WHEN prescribes_flag = 'Y'
                     AND date(dea_expiry_date) IS NOT NULL
                     AND date(dea_expiry_date) < date('2026-10-03')
                THEN 1 ELSE 0 END AS expired_dea,
           CASE WHEN prescribes_flag = 'Y'
                     AND (dea_expiry_date IS NULL OR trim(dea_expiry_date) = '')
                THEN 1 ELSE 0 END AS missing_dea,
           CASE WHEN date(caqh_attestation_date) IS NOT NULL
                     AND date(caqh_attestation_date) < date('2026-10-03', '-120 days')
                THEN 1 ELSE 0 END AS stale_caqh,
           CASE WHEN caqh_attestation_date IS NULL OR trim(caqh_attestation_date) = ''
                THEN 1 ELSE 0 END AS missing_caqh,
           CASE WHEN board_certification_status IN ('Lapsed', 'Not Certified')
                THEN 1 ELSE 0 END AS bad_board
    FROM providers
),
scored AS (
    SELECT specialty,
           (bad_npi + missing_license_no + expired_license + expired_dea
            + missing_dea + stale_caqh + missing_caqh + bad_board) AS issue_count
    FROM flags
)
SELECT specialty,
       COUNT(*) AS providers,
       SUM(CASE WHEN issue_count > 0 THEN 1 ELSE 0 END) AS providers_with_issues,
       ROUND(100.0 * SUM(CASE WHEN issue_count > 0 THEN 1 ELSE 0 END) / COUNT(*), 1)
           AS pct_with_issues
FROM scored
GROUP BY specialty
ORDER BY pct_with_issues DESC;

-- Q12. Worst offenders: providers with 2+ data-quality issues (start cleanup here)
WITH flags AS (
    SELECT row_id, provider_name, specialty, state,
           CASE WHEN npi IS NULL OR trim(npi) = ''
                     OR length(trim(npi)) <> 10
                     OR trim(npi) GLOB '*[^0-9]*'
                THEN 1 ELSE 0 END AS bad_npi,
           CASE WHEN trim(license_number) = '' OR license_number IS NULL
                THEN 1 ELSE 0 END AS missing_license_no,
           CASE WHEN date(license_expiry_date) IS NOT NULL
                     AND date(license_expiry_date) < date('2026-10-03')
                THEN 1 ELSE 0 END AS expired_license,
           CASE WHEN prescribes_flag = 'Y'
                     AND date(dea_expiry_date) IS NOT NULL
                     AND date(dea_expiry_date) < date('2026-10-03')
                THEN 1 ELSE 0 END AS expired_dea,
           CASE WHEN prescribes_flag = 'Y'
                     AND (dea_expiry_date IS NULL OR trim(dea_expiry_date) = '')
                THEN 1 ELSE 0 END AS missing_dea,
           CASE WHEN date(caqh_attestation_date) IS NOT NULL
                     AND date(caqh_attestation_date) < date('2026-10-03', '-120 days')
                THEN 1 ELSE 0 END AS stale_caqh,
           CASE WHEN caqh_attestation_date IS NULL OR trim(caqh_attestation_date) = ''
                THEN 1 ELSE 0 END AS missing_caqh,
           CASE WHEN board_certification_status IN ('Lapsed', 'Not Certified')
                THEN 1 ELSE 0 END AS bad_board
    FROM providers
)
SELECT row_id, provider_name, specialty, state,
       (bad_npi + missing_license_no + expired_license + expired_dea
        + missing_dea + stale_caqh + missing_caqh + bad_board) AS issue_count,
       TRIM(
         CASE WHEN bad_npi=1 THEN 'bad_npi; ' ELSE '' END ||
         CASE WHEN missing_license_no=1 THEN 'missing_license_no; ' ELSE '' END ||
         CASE WHEN expired_license=1 THEN 'expired_license; ' ELSE '' END ||
         CASE WHEN expired_dea=1 THEN 'expired_dea; ' ELSE '' END ||
         CASE WHEN missing_dea=1 THEN 'missing_dea; ' ELSE '' END ||
         CASE WHEN stale_caqh=1 THEN 'stale_caqh; ' ELSE '' END ||
         CASE WHEN missing_caqh=1 THEN 'missing_caqh; ' ELSE '' END ||
         CASE WHEN bad_board=1 THEN 'bad_board' ELSE '' END
       , '; ') AS issues
FROM flags
WHERE (bad_npi + missing_license_no + expired_license + expired_dea
       + missing_dea + stale_caqh + missing_caqh + bad_board) >= 2
ORDER BY issue_count DESC, row_id;
