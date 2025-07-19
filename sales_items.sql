DECLARE last_run TIMESTAMP;
SET last_run = (
    SELECT datetime 
    FROM dmt.sales_items 
    ORDER BY datetime DESC 
    LIMIT 1
);
--pour un besoin simple on dit que c'est incrementale, mais on peut évoluer
INSERT INTO dmt.sales_items
SELECT 
    CONCAT(CAST(s.id AS STRING), '-', item.product_sku) AS id, 
    s.datetime AS sales_datetime,
    item.amount AS item_amount,
    item.product_sku,
    s.quantity AS item_quantity,
    p.description AS product_description,
    ROUND(
        (p.unit_amount - (item.amount / item.quantity)) / p.unit_amount * 100
    ,2) AS discount_perc,
    CURRENT_TIMESTAMP() AS SYS_DATE_CREATE,
FROM ods.sales s
CROSS JOIN UNNEST(s.items) AS item
--Exclusion des orphan 
INNER JOIN ods.products p ON item.product_sku = p.product_sku
INNER JOIN ods.customers c ON s.customer_id = c.customer_id  
