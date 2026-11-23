# Corpus

Decided on 2026-11-23 (plan step 1.1).

## Source

- **Site:** [oesterreich.gv.at](https://www.oesterreich.gv.at), the Austrian public guidance pages.
- **Language:** German (`/de/` pages). Only 380 of the 13,325 sitemap entries have an English version, so
  English pages are not used.
- **Why this one:** the work carries over to the Amtsdeutsch helper, the licence is clear, and overlapping
  topics give multi-page answers and look-alike pages for the hard questions.

## Selection

Topic pages (`/de/themen/<topic>/...`) of five topics, taken from the site's
[sitemap](https://www.oesterreich.gv.at/sitemap.xml) as read on 2026-11-23:

| Topic | Path segment | Pages |
|-------|--------------|-------|
| Family and partnership | `familie_und_partnerschaft` | 263 |
| Work, occupation and pension | `arbeit_beruf_und_pension` | 199 |
| Getting help and financial support | `hilfe_und_finanzielle_unterstuetzung_erhalten` | 115 |
| Personal documents and certificates | `persoenliche_dokumente_und_bestaetigungen` | 86 |
| People from other countries | `menschen_aus_anderen_staaten` | 84 |
| **Total** | | **747** |

Not included: the other 16 topics, the authority and form searches (`orgsearch`, `formsearch`), the glossary
(`lexicon`), the life-situation overview pages (`lebenslagen`) and the legal news.

Pages that only list links to other pages carry no answer text and are dropped by the loader, so the final
document count will be lower than 747. It must stay within 200–1,000.

## Licence and attribution

- **Licence:** all texts are published under
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/legalcode.de), according to the site's
  [Impressum](https://www.oesterreich.gv.at/de/ueber-oesterreichgvat/impressum) ("Geistiges Eigentum", read
  2026-11-23). Personal data, photos, audio, video, logos and the page layout are excluded, so only text is
  stored.
- **Attribution:** each page ends with "Letzte Aktualisierung: <date>" and "Für den Inhalt verantwortlich:
  <owner>". Both are kept in the document metadata, together with the page URL.
- **Crawling:** `robots.txt` does not disallow the topic pages and sets no crawl delay. The fetch still
  pauses between requests and runs once.
- **Disclaimer:** the site gives general information without guarantee of correctness or currency. The
  snapshot is a test corpus, not advice.

## Questions

- The golden questions are run in German, to match the corpus.
- Marc writes each question and its expected answer in English and picks the pages that contain the answer.
  Claude writes the German version, and Marc reviews it.
- Both versions are stored. The English originals allow a later cross-language run against the same corpus.

The questions live in `questions/golden-v1.jsonl`, one JSON object per line (blank lines are allowed):

```json
{"id": "q001", "text": "<German question>", "text_en": "<English original>", "expected_answer": "<answer>", "expected_document_ids": ["<document ID>"], "tags": ["distractor"]}
{"id": "q002", "text": "<German question>", "text_en": "<English original>", "answerable": false}
```

- `expected_document_ids` lists every document that contains the answer. Optional `expected_passages`
  (`{"document_id": ..., "text": ...}`) quote the exact sentences.
- A question with `"answerable": false` has no answer in the corpus and lists no answer or documents.
- `tags` are free labels for slicing the report later.

Check the file at any time while writing:

```sh
.venv/bin/rag-bakeoff check-questions
```

It lists every problem with its line or question ID: misspelt or missing fields, a question ID used twice,
a document ID that is not in the corpus, and a question that expects only one of several documents with
identical text.

## Snapshot

Fetch the pages once, from the repo root:

```sh
.venv/bin/rag-bakeoff fetch
```

It reads the sitemap, downloads every selected page that is not stored yet (one request per second) and
writes to `data/raw/`: the pages as `pages/<hash of the URL>.html.gz`, and `manifest.jsonl` with one line
per page (URL, file, fetch time, SHA-256 of the page). If it stops on an error, run it again; it continues
where it stopped.

Then turn the raw pages into documents:

```sh
.venv/bin/rag-bakeoff load
```

It checks every stored page against the manifest, then writes `data/corpus/documents.jsonl`, sorted by ID.
The same raw files always give the same file.

- **ID:** the page's path below `/de/themen/`, for example
  `persoenliche_dokumente_und_bestaetigungen/reisepass/Seite.020100`.
- **Text:** the page body with one line per paragraph, heading (`## `, `### `), list item (`- `) or table
  row (cells joined with ` | `). Navigation, the title block and the footer are not part of it.
- **Metadata:** `topic`, `last_updated`, `owner` and `fetched_at`.
- **Left out, link lists:** pages where bare links outnumber all other blocks and the remaining text is
  under 400 characters, which is about the length of a teaser.
- **Left out, English:** the 8 pages below `menschen_aus_anderen_staaten/Information-in-English`.

Known oddities in this snapshot:

- Four documents have the same text as another one, because the site publishes the same page under two
  paths (for example a name-change notice under both marriage and divorce). A question answered by such a
  page must list both IDs.
- Two pages were served with English headings and labels around their German text
  (`persoenliche_dokumente_und_bestaetigungen/reisepass/Seite.020100` is one of them).

- **Snapshot date:** 2026-11-23 (fetched 13:37–13:52 UTC)
- **Raw pages fetched:** 747, 32 MB gzipped in `data/raw/`
- **Documents after loading:** 587 in `data/corpus/documents.jsonl` (2 MB); 152 link lists and 8 English
  pages left out
