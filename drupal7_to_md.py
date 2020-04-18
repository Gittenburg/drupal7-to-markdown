#!/usr/bin/env python3
from pathlib import Path
import csv
from datetime import datetime
import collections
import re
import html
import subprocess
import argparse
from io import StringIO

import ftfy
from html2text import HTML2Text
import yaml
import lxml.html
import lxml.etree as ET

parser = argparse.ArgumentParser(description='Convert Drupal 7 CSV to Markdown')
parser.add_argument('-d', dest='domain_regex', metavar='domain_regex', help='if given absolute links are made relative')
args = parser.parse_args()

def make_relative(url):
	if args.domain_regex:
		return re.sub('https?://{}/'.format(args.domain_regex), '/', url)
	else:
		return url

Path('published/posts').mkdir(exist_ok=True, parents=True)
Path('published/pages').mkdir(exist_ok=True)
Path('unpublished/posts').mkdir(exist_ok=True, parents=True)
Path('unpublished/pages').mkdir(exist_ok=True)

node2alias = collections.defaultdict(list)

# HTML2Text does not discards HTML comments so we monkey-patch it:
HTML2Text.handle_comment = lambda self, data: self.out('<!--{}-->'.format(data))

with open('url_alias.csv') as f:
	for line in f:
		a, b = line.strip().split('\t')
		if not a.startswith('node/'):
			continue
		node2alias[a[5:]].append(b)

with open('redirects.csv') as f:
	for line in f:
		b, a = line.strip().split('\t')
		if not a.startswith('node/'):
			continue
		if re.search(r'https?://', b):
			print('skipping external redirect', a, b)
		node2alias[a[5:]].append(b)

attachments = collections.defaultdict(list)

with open('attachments.csv') as f:
	for line in f:
		nid, path, name = line.strip().split('\t')
		attachments[nid].append((name, '/' + path))

with open('nodes.csv', newline='') as csvfile:
	# Windows line endings weirdly confuse csv.reader() so we remove them
	csvfile = StringIO(csvfile.read().replace('\r', ''))

	reader = csv.reader(csvfile, 'unix', delimiter='\t', lineterminator='\n')
	next(reader) # skip CSV header

	for row in reader:
		nid, type, title, status, created, changed, body_value, body_format, tags, author = row

		if len(body_value) == 0:
			continue

		if status == '0':
			path = 'unpublished/'
		else:
			path = 'published/'

		# TODO: make types configurable

		# clean up data
		title = ftfy.fix_text(title).strip()
		date = str(datetime.fromtimestamp(int(created)))
		body_value = ftfy.fix_text(body_value.replace('\\t', '\t').replace('\\n', '\n')).strip()

		if body_format in ('1', '3'): # filtered and full html
			body_value = subprocess.check_output('./autop.php', input=body_value, encoding='utf-8')

		legacy = list(dict.fromkeys(node2alias[nid]))

		if len(legacy) == 0 or re.search(r'\d{6}', legacy[0]) or re.search(r'[^a-zA-Z0-9_äüöß-]+', legacy[0]):
			slug = re.sub(r'[^a-zA-Z0-9_äüöß]+', '-', title.lower()).strip('-')
		else:
			slug = legacy[0]

		if type == 'page' and int(nid):
			path += 'pages/' + slug + '.md'
		else:
			path += 'posts/' + date[:10] + '-' + slug + '.md'

		body_value = re.sub(r'<!-- *(break|more) *-->', '<!--more-->', body_value)

		hasMore = '<!--more-->' in body_value

		if '<?php' in body_value:
			print('found PHP tag:', path)
			body_value = re.sub(r'<\?php.*?\?>', lambda m: '<pre>' + html.escape(m.group(0)) + '</pre>', body_value, flags=re.DOTALL)

		doc = lxml.html.fromstring(body_value)

		if not hasMore and '/posts/' in path and len(doc) > 2:
			doc.insert(2, ET.Comment('more'))

		# extract thumbnails
		img = doc.xpath('.//img[@src]')
		if len(img) > 0 and '/posts/' in path:
			img = img[0]
			img_src = make_relative(img.get('src')).lstrip('/')
			if img_src.startswith('files/'):
				img_src = img_src[len('files/'):]
			else:
				print('invalid image: {}'.format(path))
			img_alt = img.get('alt')
			img.drop_tree()
		else:
			img_src = None
			img_alt = None

        # make absolute links relative
		doc.rewrite_links(make_relative)

		body_value = lxml.html.tostring(doc, encoding='unicode')

		body_value = HTML2Text(bodywidth=0).handle(body_value)
		body_value = re.sub('\n\n$', '\n', body_value, flags=re.M)

		if Path(path).exists():
			path += '-DUPLICATE.md'

		with open(path, 'w') as f:
			# using yaml.dump only for single fields because it does not maintain order
			f.write('---\n')
			f.write(yaml.dump(dict(title=title), allow_unicode=True))
			f.write('date: %s\n' % date)
			if author:
				f.write('author: %s\n' % author)
			if tags != 'NULL':
				f.write('tags: [%s]\n' % tags)
			if img_src:
				f.write('image: %s\n' % img_src)
			if img_alt:
				f.write(yaml.dump(dict(image_alt=img_alt), allow_unicode=True))
			f.write('legacy-links:\n')
			for l in legacy:
				f.write('  - %s\n' % l)
			f.write('  - node/%s\n' % nid)
			f.write('---\n')
			f.write(body_value)

			if attachments[nid]:
				f.write('\n\nAttachments:\n\n')
				for att in attachments[nid]:
					f.write('* [%s](%s)\n' % att)
