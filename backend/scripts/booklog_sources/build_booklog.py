#!/usr/bin/env python3
"""모든 출처를 합쳐 backend/data/booklog_purchases.json 을 만든다.

출처
  google_sites  Google Sites Booklog 2010–2017 연도별 표
  backdata      배경여행 DB.xlsx 의 BACKDATA 시트 (2010–2018 마스터)
  kyobo         교보문고 주문내역 (2021–2026)
  millie        밀리의 서재 내서재 (구독)
  audible_jp    Audible Japan 라이브러리 (구독)

google_sites 와 backdata 는 같은 구매 기록이 갈라진 것이라 (연도, 제목) 으로 합집합 병합한다.
나머지는 서로 다른 경로로 얻은 책이라 그대로 둔다.
"""
from __future__ import annotations

import difflib
import itertools
import json
import re
from collections import Counter

OUT = "booklog_all.json"

SRC_GSITES = "booklog_gsites.json"
SRC_BACKDATA = "backdata_raw.json"
SRC_KYOBO = "kyobo_raw.tsv"
SRC_KYOBO_ENRICH = "kyobo_enrich.tsv"
SRC_MILLIE = ["millie_acct1.txt", "millie_acct2.txt"]
SRC_AUDIBLE = "audible_jp.txt"

# Audible 라이브러리 중 팟캐스트(도서 아님)
AUDIBLE_PODCASTS = {"B0CVQ4ZB7N", "B0F6KPT9PS", "B0DXVCQ5XD"}

# 교보 주문 중 도서가 아니거나 반품된 건
KYOBO_SKIP_KINDS = {"판매옵션상품", "sam이용권"}
KYOBO_SKIP_STATUS = {"반품완료", "취소완료", "품절"}

MILLIE_CATEGORY = {"10": "읽고 싶은 책", "20": "읽는 중", "30": "완독"}

_norm_re = re.compile(r"[\s()\[\]{}.,·:;!?\-–—_/'\"*]+")
# Google Sites 쪽에만 붙어 있는 말머리: [일서], [양서해외주문] 등
_tag_re = re.compile(r"^(?:\[[^\]]{1,12}\]\s*)+")


def norm_title(s: str | None) -> str:
    return _norm_re.sub("", _tag_re.sub("", str(s or ""))).lower()


def clean(v) -> str | None:
    if v is None:
        return None
    v = re.sub(r"\s+", " ", str(v)).strip()
    return v or None


def ymd(raw: str | None, fallback_year: int | None = None) -> str | None:
    """'20150104' / '2010년 1월' / '2015-01-04 12:00:00' -> 'YYYY-MM-DD' 또는 'YYYY-MM'."""
    s = (raw or "").strip()
    if not s:
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    if re.fullmatch(r"\d{8}", s):
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    if re.fullmatch(r"\d{6}", s):
        return f"{s[:4]}-{s[4:6]}"
    m = re.search(r"(\d{4})\s*년\s*(\d{1,2})\s*월(?:\s*(\d{1,2})\s*일)?", s)
    if m:
        y, mo, d = m.group(1), int(m.group(2)), m.group(3)
        return f"{y}-{mo:02d}-{int(d):02d}" if d else f"{y}-{mo:02d}"
    m = re.search(r"(\d{1,2})\s*월", s)
    if m and fallback_year:
        return f"{fallback_year}-{int(m.group(1)):02d}"
    return None


def rec(**kw) -> dict:
    base = {
        "year": None,
        "title": None,
        "author": None,
        "translator": None,
        "publisher": None,
        "published": None,
        "purchase_date": None,
        "isbn": None,
        "cover_url": None,
        "note": None,
        "source": None,
        "source_url": None,
        "source_ref": None,
        "sort_order": 0,
    }
    base.update(kw)
    return base


# --------------------------------------------------------------------------- 출처별 로더


def load_gsites() -> list[dict]:
    data = json.load(open(SRC_GSITES))
    out = []
    for year_str, rows in data.items():
        year = int(year_str)

        header = [c.strip() for c in rows[0]]
        idx = {n: i for i, n in enumerate(header)}

        def pick(cells, *names):
            for n in names:
                i = idx.get(n)
                if i is not None and i < len(cells):
                    return clean(cells[i])
            return None

        order = 0
        for cells in rows[1:]:
            title = pick(cells, "상품명", "작품명")
            if not title:
                continue
            order += 1
            seq = pick(cells, "번호") or str(order)
            out.append(
                rec(
                    year=year,
                    title=title,
                    author=pick(cells, "지은이", "지은이 / 감독"),
                    translator=pick(cells, "옮긴이"),
                    publisher=pick(cells, "출판사"),
                    published=ymd(pick(cells, "출판년월", "출판/개봉년월"), year),
                    purchase_date=ymd(pick(cells, "구매일자"), year),
                    note=pick(cells, "이야기"),
                    source="google_sites",
                    # 연도 페이지 링크라 책 한 권을 가리키지도 않고, 사이트에서 Google Sites
                    # 링크를 모두 걷어내기로 해서 남기지 않는다.
                    source_url=None,
                    source_ref=f"google_sites:{year}:{seq}",
                    sort_order=order,
                )
            )
    return out


def load_backdata() -> list[dict]:
    rows = json.load(open(SRC_BACKDATA))
    out = []
    order = Counter()
    for i, r in enumerate(rows):
        if r.get("분류") != "책":  # 영화·드라마 제외
            continue
        title = clean(r.get("작품명"))
        if not title:
            continue
        year = int(r["구매연도"]) if r.get("구매연도") else None
        if year:
            order[year] += 1
        out.append(
            rec(
                year=year,
                title=title,
                author=clean(r.get("지은이 / 감독")),
                publisher=clean(r.get("출판사")),
                published=ymd(r.get("출판/개봉년월"), year),
                purchase_date=ymd(r.get("구매일자"), year),
                source="backdata",
                source_url=clean(r.get("작품링크")),
                source_ref=f"backdata:{i}",
                sort_order=order[year] if year else 0,
            )
        )
    return out


def load_kyobo() -> list[dict]:
    enrich: dict[str, tuple[str | None, str | None]] = {}
    for line in open(SRC_KYOBO_ENRICH, encoding="utf-8"):
        if not line.strip():
            continue
        c = line.rstrip("\n").split("\t")
        pub = c[2].strip() if len(c) > 2 and c[2].strip() else None
        enrich[c[0]] = (c[1].strip() if len(c) > 1 and c[1].strip() else None, ymd(pub))

    out, seen = [], set()
    for line in open(SRC_KYOBO, encoding="utf-8"):
        cells = line.rstrip("\n").split("\t")
        if len(cells) < 7:  # 사은품 행(출판사 없음)
            continue
        date, raw_title, publisher, isbn, pid, kind, status = cells[:7]
        if kind in KYOBO_SKIP_KINDS or status in KYOBO_SKIP_STATUS:
            continue
        ref = f"kyobo:{date}:{pid}"
        if ref in seen:
            continue
        seen.add(ref)

        fmt = None
        m = re.match(r"^\[([^\]]+)\]\s*", raw_title)
        if m:
            fmt = m.group(1)
            raw_title = raw_title[m.end() :]
        rental = raw_title.startswith("[대여]")
        raw_title = re.sub(r"^\[대여\]\s*", "", raw_title)

        notes = [n for n in (fmt if fmt and fmt != "국내도서" else None, "대여" if rental else None) if n]
        author, published = enrich.get(pid, (None, None))
        detail = (
            f"https://ebook-product.kyobobook.co.kr/dig/epd/ebook/{pid}"
            if pid.startswith("E")
            else f"https://product.kyobobook.co.kr/detail/{pid}"
        )
        out.append(
            rec(
                year=int(date[:4]),
                title=clean(raw_title),
                author=author,
                publisher=clean(publisher),
                published=published,
                purchase_date=f"{date[:4]}-{date[4:6]}-{date[6:8]}",
                isbn=isbn or None,
                cover_url=f"https://contents.kyobobook.co.kr/sih/fit-in/300x0/pdt/{isbn}.jpg"
                if isbn
                else None,
                note=" · ".join(notes) or None,
                source="kyobo",
                source_url=detail,
                source_ref=ref,
            )
        )
    return out


def load_millie() -> list[dict]:
    import os

    out = []
    for path in SRC_MILLIE:
        if not os.path.exists(path):
            continue
        acct = re.search(r"acct(\d+)", path).group(1)
        for line in open(path, encoding="utf-8"):
            if not line.strip():
                continue
            c = [x.strip() for x in line.rstrip("\n").split("~|")]
            if len(c) < 10:
                continue
            read_at, created_at, category, percent, title, author, publisher, published, bid, audio = c[:10]
            when = read_at or created_at
            notes = [MILLIE_CATEGORY.get(category, "")]
            if percent:
                notes.append(f"{percent}%")
            if audio == "audio":
                notes.append("오디오북")
            if len(SRC_MILLIE) > 1 and acct != "1":
                notes.append(f"계정{acct}")
            out.append(
                rec(
                    year=int(when[:4]) if when else None,
                    title=clean(title),
                    author=clean(author),
                    publisher=clean(publisher),
                    published=ymd(published),
                    purchase_date=ymd(when),
                    note=" · ".join(n for n in notes if n) or None,
                    source="millie",
                    source_ref=f"millie:{acct}:{bid}",
                )
            )
    return out


def load_audible() -> list[dict]:
    out = []
    for line in open(SRC_AUDIBLE, encoding="utf-8"):
        if not line.strip():
            continue
        c = [x.strip() for x in line.rstrip("\n").split("~|")]
        if len(c) < 7:
            continue
        _, asin, title, author, narrator, length, done = c[:7]
        if asin in AUDIBLE_PODCASTS:
            continue
        notes = ["오디오북"]
        if narrator:
            notes.append(f"낭독 {narrator}")
        if length:
            notes.append(length)
        if done:
            notes.append("청취 완료")
        out.append(
            rec(
                year=None,  # Audible 은 구독 이용이라 주문 기록이 없다
                title=clean(title),
                author=clean(author),
                note=" · ".join(notes),
                source="audible_jp",
                source_url=f"https://www.audible.co.jp/pd/{asin}",
                source_ref=f"audible_jp:{asin}",
            )
        )
    return out


# --------------------------------------------------------------------------- 병합


MIN_PREFIX_LEN = 4  # 이보다 짧은 제목은 접두사 비교를 하지 않는다 ("대망" 같은 총서명 오병합 방지)
_VOLUME_RE = re.compile(r"^\d+(권|화|부|편)?$")  # 잘린 뒤가 권차만 남는 경우: "2", "3권"


def prefix_match(short: str, long: str) -> bool:
    """한쪽 제목이 다른 쪽의 잘린 형태인지.

    제목 뒤에 '(개정판)', '(세계문학전집 214)', '(10주년 기념 개정판)' 같은 꼬리표가
    붙거나 빠진 채로 기록된 경우가 많다. 다만 남는 부분이 권차뿐이면
    ('정약용과 그의 형제들' vs '…2') 다른 권이므로 병합하지 않는다.
    """
    if len(short) < MIN_PREFIX_LEN or not long.startswith(short):
        return False
    rest = long[len(short) :]
    return not _VOLUME_RE.match(rest)


def merge_logs(primary: list[dict], secondary: list[dict]) -> list[dict]:
    """같은 구매 기록이 갈라진 두 출처를 (연도, 제목) 으로 합집합 병합.

    primary 를 남기고, 겹치는 항목은 secondary 의 빈 칸만 채워 넣는다.
    """
    by_key: dict[tuple, dict] = {}
    by_year: dict[int | None, list[tuple[str, dict]]] = {}
    merged = []
    for r in primary:
        t = norm_title(r["title"])
        by_key[(r["year"], t)] = r
        by_year.setdefault(r["year"], []).append((t, r))
        merged.append(r)

    filled = exact = prefix = 0
    for r in secondary:
        t = norm_title(r["title"])
        hit = by_key.get((r["year"], t))
        if hit is not None:
            exact += 1
        else:
            for other_t, other in by_year.get(r["year"], []):
                if prefix_match(t, other_t) or prefix_match(other_t, t):
                    hit = other
                    prefix += 1
                    break
        if hit is None:
            by_key[(r["year"], t)] = r
            by_year.setdefault(r["year"], []).append((t, r))
            merged.append(r)
            continue
        for f in ("author", "translator", "publisher", "published", "purchase_date", "note", "isbn"):
            if not hit.get(f) and r.get(f):
                hit[f] = r[f]
                filled += 1
    print(f"  중복 제거: 제목 일치 {exact}건 + 잘린 제목 {prefix}건 / 빈 칸 채움 {filled}개")
    return merged


SOURCE_LABEL = {
    "backdata": "배경여행 DB",
    "google_sites": "Google Sites",
    "kyobo": "교보문고",
    "millie": "밀리의 서재",
    "audible_jp": "Audible Japan",
}

_author_split_re = re.compile(r"[/,·]|\s지음|\s저자|\s원작|\s엮음|\s글|\(")
_author_role_re = re.compile(r"(저|역|글|작|편|지음|엮음|옮김)+$")


def norm_author(s: str | None) -> str:
    """대표 저자만 남겨 비교용으로 정규화. '오가와 이토 지음 / 이지수 옮김' -> '오가와이토'."""
    first = _author_split_re.split(str(s or ""))[0]
    return _author_role_re.sub("", re.sub(r"[\s.]+", "", first).lower())


FILLABLE = ("author", "translator", "publisher", "published", "isbn", "cover_url", "source_url")
AUTHOR_SIMILARITY = 0.8  # 제목이 같을 때 저자 표기가 이 정도 닮았으면 같은 책으로 본다
_percent_re = re.compile(r"(\d+)%")


def read_percent(r: dict) -> int:
    """비고에 적힌 읽은 비율. 없으면 -1."""
    m = _percent_re.search(r.get("note") or "")
    return int(m.group(1)) if m else -1


def dedupe_books(records: list[dict]) -> list[dict]:
    """같은 책이 여러 번 들어간 것을 한 건으로 합친다.

    같은 책을 종이책으로 샀다가 오디오북으로 다시 읽거나, eBook 판과 오디오북 판이 따로
    잡히거나, 밀리 계정 두 곳에 모두 있는 경우가 있다. 가장 먼저 기록된 것을 남기고
    나머지는 비고에 '다른 기록' 으로 적어 둔다.
    """
    groups: dict[tuple[str, str], list[dict]] = {}
    for r in records:
        groups.setdefault((norm_title(r["title"]), norm_author(r["author"])), []).append(r)

    # 같은 저자 안에서 제목이 잘린 형태인 키끼리 한 번 더 합친다
    by_author: dict[str, list[str]] = {}
    for title_key, author_key in groups:
        by_author.setdefault(author_key, []).append(title_key)
    for author_key, titles in by_author.items():
        if not author_key:
            continue
        for short, long in itertools.permutations(sorted(titles, key=len), 2):
            if short in titles and long in titles and prefix_match(short, long):
                groups[(long, author_key)].extend(groups.pop((short, author_key)))
                titles.remove(short)

    # 제목이 똑같은데 저자 표기만 살짝 다른 경우 ('루이자 메이 올컷' vs '올콧') 도 같은 책으로 본다
    by_title: dict[str, list[str]] = {}
    for title_key, author_key in groups:
        by_title.setdefault(title_key, []).append(author_key)
    for title_key, authors in by_title.items():
        if not title_key:
            continue
        for a, b in itertools.combinations(sorted(authors), 2):
            if a not in authors or b not in authors or not a or not b:
                continue
            if difflib.SequenceMatcher(None, a, b).ratio() >= AUTHOR_SIMILARITY:
                groups[(title_key, a)].extend(groups.pop((title_key, b)))
                authors.remove(b)

    out, removed = [], 0
    for (title_key, _), items in groups.items():
        if len(items) == 1 or not title_key:
            out.extend(items)
            continue

        # 가장 먼저 기록된 것을 대표로 남긴다 (연도·비고가 서로 어긋나지 않도록)
        items.sort(key=lambda r: (r["purchase_date"] or "9999", r["year"] or 9999))
        base, others = items[0], items[1:]
        for other in others:
            for f in FILLABLE:
                if not base.get(f) and other.get(f):
                    base[f] = other[f]

        # 읽은 진도는 가장 많이 읽은 기록을 남긴다 (eBook 81% + 오디오북 완독이면 완독)
        best = max(items, key=read_percent)
        note = best["note"] if read_percent(best) > read_percent(base) else base.get("note")

        # 대표와 연도·출처가 같은 건 굳이 적지 않는다 (같은 책의 eBook·오디오북 판 등)
        labels = []
        for other in others:
            if (other["year"], other["source"]) == (base["year"], base["source"]):
                continue
            label = SOURCE_LABEL.get(other["source"], other["source"] or "")
            labels.append(f"{other['year']} {label}" if other["year"] else label)
        labels = list(dict.fromkeys(labels))
        parts = [note]
        if labels:
            parts.append("다시 읽음: " + ", ".join(labels))
        base["note"] = " · ".join(filter(None, parts)) or None

        out.append(base)
        removed += len(others)

    print(f"  같은 책 병합: {removed}건 제거")
    return out


def main() -> None:
    gsites = load_gsites()
    backdata = load_backdata()
    kyobo = load_kyobo()
    millie = load_millie()
    audible = load_audible()

    print(f"google_sites {len(gsites)} / backdata {len(backdata)}")
    combined = merge_logs(backdata, gsites)
    print(f"  -> 병합 후 {len(combined)}")

    records = dedupe_books(combined + kyobo + millie + audible)

    # 연도별 정렬 순서 부여 (구매일 오름차순)
    per_year: Counter = Counter()
    for r in sorted(records, key=lambda x: (x["year"] or 0, x["purchase_date"] or "")):
        per_year[r["year"]] += 1
        r["sort_order"] = per_year[r["year"]]

    json.dump(records, open(OUT, "w"), ensure_ascii=False, indent=1)

    print()
    print(f"총 {len(records)}건")
    for s, n in Counter(r["source"] for r in records).most_common():
        print(f"  {s}: {n}")
    print()
    print("연도별:", dict(sorted(Counter(r["year"] for r in records).items(), key=lambda x: (x[0] is None, x[0]))))
    refs = Counter(r["source_ref"] for r in records)
    print("source_ref 중복:", sum(v - 1 for v in refs.values() if v > 1))
    print("제목 없음:", sum(1 for r in records if not r["title"]))
    print("저자 없음:", sum(1 for r in records if not r["author"]))


if __name__ == "__main__":
    main()
