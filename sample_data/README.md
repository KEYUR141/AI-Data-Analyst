# Synthetic test datasets

Upload `retail_sales.csv` for a richer test, or `sales.csv` for a five-row smoke check. All records are fictional. Revenue has no currency designation; treat it as generic monetary units.

`retail_sales.csv` contains 121 rows across January–June 2026, four regions/products, twelve customer IDs, quantity, price, revenue, and sales channel. One row is repeated exactly; one revenue and one customer ID are missing. Order ORD-0011 has an intentionally inconsistent revenue of 12000 to exercise future anomaly detection. Keep customer IDs as text.

`retail_sales_expected.json` records independently calculated checks. Region totals include the duplicate and outlier, and ignore the blank revenue. Overall revenue is 61720; South leads with 27000. If cleaning or deduplication is applied, these totals must change explicitly.

Try these planning questions:

- Which region generated the highest revenue?
- Show monthly revenue trends as a line chart.
- What are the top five customers by revenue?
- Compare revenue by product in a bar chart.
- Which products are underperforming? (Should clarify the criterion.)

Missing values and duplicates can be checked in profiling now. Anomaly detection and query execution are not implemented yet; do not expect generated plans to execute.
