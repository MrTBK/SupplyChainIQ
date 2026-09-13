# Power BI model notes

Source: warehouse marts (008_marts.sql) via Postgres (prod) or CSV export of views (demo). Mark DimDate as date table. Relationships: dim_product[product_sk]→facts, dim_warehouse, dim_supplier, dim_customer, dim_carrier, dim_date[date_key]→fact date keys (inactive extra date roles where needed). Import only needed columns; target < 500MB demo. Incremental refresh ready on date_key monthly.
