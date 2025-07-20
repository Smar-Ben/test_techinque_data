DECLARE last_run TIMESTAMP DEFAULT(
    COALESCE(
        (
            SELECT MAX(sales_datetime) 
            FROM dmt.sales_items
        ),
        DATETIME('1980-01-01')  
    )
);
--pour un besoin simple on dit que c'est incrementale, mais on peut évoluer
INSERT INTO dmt.sales_items (
    id, 
    sales_datetime,
    item_amount,
    product_sku,
    item_quantity,
    product_description,
    discount_perc,
    SYS_DATE_CREATE,
)
SELECT 
    CONCAT(CAST(s.id AS STRING), '-', item.product_sku) AS id, 
    s.datetime AS sales_datetime,
    item.amount AS item_amount,
    item.product_sku,
    item.quantity AS item_quantity,
    p.description AS product_description,
    ROUND(
        (p.unit_amount - (item.amount / item.quantity)) / p.unit_amount * 100
    ,2) AS discount_perc,
    CURRENT_TIMESTAMP() AS SYS_DATE_CREATE,
FROM ods.sales s
CROSS JOIN UNNEST(s.items) AS item
--Exclusion des orphan même pour les customers
INNER JOIN ods.products p ON item.product_sku = p.product_sku
INNER JOIN ods.customers c ON s.customer_id = c.customer_id  
WHERE s.datetime>last_run
