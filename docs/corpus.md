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

## Snapshot

Filled in when the corpus is fetched and loaded (plan steps 1.3 and 1.4).

- **Snapshot date:** not fetched yet
- **Raw pages fetched:** not fetched yet
- **Documents after loading:** not loaded yet
