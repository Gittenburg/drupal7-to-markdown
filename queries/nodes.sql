SELECT
    n.nid,
    type,
    title,
    n.status, -- 0 = not published, 1 = published
    n.created,
    changed,
    b.body_value,
    b.body_format,
    group_concat(replace(lower(tt.name), ' ', '-') separator ', ') as tags,
    users.name
FROM node n
JOIN field_data_body b ON n.nid=entity_id
LEFT JOIN taxonomy_index t ON n.nid=t.nid
LEFT JOIN taxonomy_term_data tt on t.tid=tt.tid
LEFT JOIN users on users.uid=n.uid
GROUP BY n.nid;
