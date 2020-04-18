# Drupal 7 to Markdown

	(╯°□°)╯︵ lɐdnɹp

This repository contains some scripts I used to convert the content from a
Drupal 7 database to Markdown files. Maybe you will find them useful.

The SQL queries were only tested with MySQL (and you will need database access
to run them). With MySQL getting the the nodes as CSV is as simple as:

	./mysql_to_csv.sh --host your_host --user your_user your_db --password=your_pw < queries/nodes.sql > nodes.csv

The database credentials can probably be found in `sites/<your_domain>/settings.php`.

## drupal7_to_md.py

The script postprocesses the exported CSV files. It requires Python 3.

The Python dependencies can be installed with `pip3 install -r requirements.txt`.

To migrate pages using the *filtered HTML* format of the [Filter
module](https://www.drupal.org/docs/7/core/modules/filter) the script uses the
bundled `autop.php` script containing the original conversion function from
Drupal.  So PHP is also required.

### Features

* The HTML is converted to Markdown with [html2text](https://github.com/Alir3z4/html2text) (monkey-patched to preserve HTML comments).
* The script generates better slugs than Drupal, which turns dates like 19.1.2015 into 1912015.
* all legacy links are preserved (both aliases and redirects)
* the first image of posts is removed from the HTML and added to the frontmatter
* shown attachments are appended as Markdown
* topology is preserved as tags in the frontmatter
* PHP tags in nodes are HTML-escaped and put in a `<pre>` tag
* published and unpublished nodes are saved in separate directories

Optional features (run the script with `-h` for the usage):

* make absolute links relative

### What this script does not do

* Handle other versions of Drupal.
* Handle other Drupal modules (e.g. comments).
* Handle files (you just need to copy the `files` directory).
* Handle external redirects (you can get them with `grep http redirects.csv`).
* Touch the database (it just operates on CSV files produced by `mysql_to_csv.sh`).
