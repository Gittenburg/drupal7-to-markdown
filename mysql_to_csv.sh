mysql $@ < queries/nodes.sql > nodes.csv
mysql $@ < queries/attachments.sql > attachments.csv
mysql $@ < queries/redirects.sql > redirects.csv
mysql $@ < queries/url_alias.sql > url_alias.csv
