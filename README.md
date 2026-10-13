# Oman — LawCodex (تشريعات سلطنة عمان)

Omani legislation as plain Markdown, in Arabic. Part of
[LawCodex](https://github.com/LawCodex): one repository per jurisdiction.

> **Source: Qanoon.om, an unofficial database.** The texts come from
> [**Qanoon.om**](https://qanoon.om), an independent, privately run database of Omani legislation
> (launched 2015). It is not a government website. It transcribes legislation from the
> **Official Gazette** (الجريدة الرسمية), published by the Ministry of Justice and Legal Affairs.
> Most files link the gazette scan that Qanoon.om hosts (`gazette_pdf`) and give the gazette
> issue (`gazette`). Check those before you rely on a text.
>
> The official site of the Ministry of Justice and Legal Affairs
> ([mjla.gov.om](https://www.mjla.gov.om)) publishes the Official Gazette only as PDF issues.
> It has no full-text, per-instrument database that could be converted. Qanoon.om's
> robots.txt allows crawling, and its site has no terms of use restricting reuse.

- Retrieved: **2026-10-13**, through Qanoon.om's public WordPress REST API (`/wp-json/wp/v2/posts`).
- Nothing is translated, summarised or edited.

## Coverage

| Directory | Contents | Files |
| --- | --- | ---: |
| `basic-statute/` | النظام الأساسي للدولة: the Basic Statute of the State (Royal Decree 6/2021), consolidated by Qanoon.om up to its latest amendment | 1 |
| `royal-decrees/<year>/` | مراسيم سلطانية: Royal Decrees, 1974–2026. These include those that promulgate laws (e.g. `rd2018007.md`, which promulgates the Penal Code), appointments, budgets and treaty ratifications. Each decree is given as published, including the law it promulgates | 4,918 |
| `consolidated-laws/<year>/` | قوانين معدلة: consolidated texts of laws, with all amendments applied by Qanoon.om ("نص معدل", e.g. the Penal Code and the Labour Law) | 102 |
| `consolidated-regulations/<year>/` | لائحة معدلة: consolidated executive regulations | 1 |
| `legacy-laws/` | قوانين تقليدية: laws issued before the royal-decree numbering, 1972–1975. Ten of them are available only as gazette scans; their files hold the title and gazette reference | 30 |
| `royal-orders/<year>/` | أوامر سامية: Royal Orders (awards, pardons, etc.) | 85 |
| `ministerial-decisions/<year>/` | قرارات وزارية: ministerial decisions and decisions of public authorities, 1973–2026 | 4,568 |
| `covid-19-committee-decisions/` | decisions of the Supreme Committee dealing with Covid-19 (2020–2022) | 83 |
| `circulars/` | تعاميم: circulars | 3 |
| **Total** | | **9,791** |

Three posts have no text (only a heading or a PDF link) and were skipped: `rd1992001`,
`rd2000001` and `msx20250139`.

### Not covered / known gaps

- **Status.** Qanoon.om does not mark repealed or expired instruments in a machine-readable way,
  so every file has `status: unknown`. Repeal and amendment notes that appear in the text are
  kept.
- **English.** Qanoon.om's sister site [decree.om](https://decree.om) publishes English
  translations of many royal decrees. They are unofficial translations, so they are not included.
  Each Arabic file that has one links it in `english_translation` (1,627 files). The Omani
  government does not publish official English translations of legislation.
- Not included: Official Gazette issue indexes, international agreements published as separate
  posts (680 posts; the royal decrees ratifying them are included), legal opinions (فتاوى) and
  court rulings.
- Annexed tables and images that Qanoon.om reproduces only as images are not included.

## Structure and file names

```
ar/basic-statute/l2021006.md
ar/<category>/<year>/<qanoon-slug>.md
```

The file name is Qanoon.om's own identifier for the instrument. It encodes the kind of instrument,
the year and the number:

- `rd2021006` is Royal Decree No. 6/2021.
- `l2018007` is the consolidated text of the law issued in 2018 under No. 7.
- `ro2015001` is a Royal Order.
- Ministerial decisions use the issuing body's prefix (e.g. `moh20260254` is Ministry of
  Health decision No. 254/2026).

The year directory is that same year.

Front matter: `title` (Arabic title), `identifier` (Qanoon.om slug), `type`, `number`,
`year`, `date` (Gregorian date of issue, from "الموافق" in the signature block, where present),
`last_amended` (consolidated texts: date of Qanoon.om's latest update), `status`,
`gazette` (Official Gazette issue and date), `gazette_pdf`, `consolidated_version`,
`english_translation`, `source`, `source_modified`, `retrieved`.

Headings: the parts of each text (الباب / الفصل / الفرع …) are headings, and each article
(المادة …) is a heading one level below.

## Licence

These are official legislative texts of the Sultanate of Oman. Under Article 4 of the Omani Law
on Copyright and Related Rights (Royal Decree 65/2008,
[`ar/royal-decrees/2008/rd2008065.md`](ar/royal-decrees/2008/rd2008065.md)), protection does
not extend to "official documents such as laws, regulations, decisions, international
agreements and treaties, judicial rulings … and official translations of any of these".
Qanoon.om's transcriptions are used with attribution: every file links its Qanoon.om page.

## Regenerating

```sh
pip install -r scripts/requirements.txt
python scripts/om_fetch.py  /path/to/raw     # pages of 50 posts per category via the WP REST API
python scripts/om_convert.py /path/to/raw .
```

The fetcher sends one request at a time, about one per second, and identifies itself as
`LawCodex/1.0`.
