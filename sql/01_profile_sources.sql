-- Quick source checks. Run each query on its own.
-- 1. Compare source rows with unique referrals.
SELECT COUNT(*) AS raw_rows, COUNT(DISTINCT referral_id) AS unique_referrals,
       COUNT(*)-COUNT(DISTINCT referral_id) AS excess_source_rows
FROM raw_referral_rows;

-- 2. Find repeated referral IDs.
SELECT referral_id,COUNT(*) AS rows_per_referral,
       MIN(source_updated_at) AS earliest_update,MAX(source_updated_at) AS latest_update
FROM raw_referral_rows GROUP BY referral_id HAVING COUNT(*)>1
ORDER BY rows_per_referral DESC,referral_id;

-- 3. List source statuses that need mapping.
SELECT LOWER(TRIM(source_status)) AS source_status_key,COUNT(*) AS source_rows
FROM raw_referral_rows GROUP BY LOWER(TRIM(source_status)) ORDER BY source_rows DESC;

-- 4. Find records with no receipt date.
SELECT source_row_id,referral_id,received_date,source_status
FROM raw_referral_rows WHERE received_date IS NULL;

-- 5. Check missing owners.
SELECT account_id,account_name FROM raw_accounts WHERE sales_rep_id IS NULL;
SELECT referral_id,source_status FROM canonical_referrals WHERE intake_owner_id IS NULL;
