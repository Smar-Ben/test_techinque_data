--requête pour voir les orphans peut être transformé en vue
SELECT 
    s.id,
    s.datetime,
    CASE 
        WHEN p.product_sku IS NULL AND c.customer_id IS NULL THEN "missing_product_customer"
        WHEN p.product_sku IS NULL THEN 'missing_product'
        WHEN c.customer_id IS NULL THEN 'missing_customer'
        ELSE 'unknown'
    END AS orphan_type,
    s.SYS_DATE_CREATE
FROM ods.sales s
LEFT JOIN UNNEST(s.items) AS i
LEFT JOIN ods.products p ON i.product_sku = p.product_sku
LEFT JOIN ods.customers c ON s.customer_id = c.customer_id
WHERE p.product_sku IS NULL OR c.customer_id IS NULL;