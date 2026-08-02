# Booklog 원천 데이터

`backend/data/booklog_purchases.json` (총 1,773건)을 만들어 낸 원본과 빌드 스크립트입니다.
평소에는 쓸 일이 없고, 원본을 다시 긁어와 데이터를 재생성할 때만 사용합니다.

## 구성

| 파일 | 내용 | 건수 |
| --- | --- | --- |
| `backdata_raw.json` | `배경여행 DB.xlsx` 의 BACKDATA 시트 (2010–2018 구매 마스터). 영화·드라마 19건 포함 | 1,250 |
| `booklog_gsites.json` | Google Sites Booklog 2010–2017 연도별 페이지에서 추출한 표 (행 = 셀 배열) | 1,186 |
| `kyobo_raw.tsv` | 교보문고 주문내역 API 응답 (2021-08 ~ 2026-08) | 139 |
| `kyobo_enrich.tsv` | 교보 상품 페이지에서 보강한 `상품ID → 저자 [→ 출간일]` | 131 |
| `millie_acct1.txt` | 밀리의 서재 현재 계정 (구분자 `~|`) | 147 |
| `millie_acct2.txt` | 밀리의 서재 이전 계정 (구분자 `~|`) | 269 |
| `audible_jp.txt` | Audible Japan 라이브러리 (구분자 `~|`) | 41 |
| `build_booklog.py` | 위 전부를 합쳐 `booklog_all.json` 생성 | 1,773 |

밀리의 서재를 계정 하나 더 쓰게 되면 `millie_acct3.txt` 처럼 번호를 올려 두면 빌드에 자동으로
포함되고, 2번 이후 계정은 비고에 `계정2` 가 붙습니다. 파일은 탭이 아니라 `~|` 로 나눕니다 —
제목·저자에 탭이 섞여 들어와 칸이 밀리는 일이 있었습니다.

## 재생성

```bash
cd backend/scripts/booklog_sources
python3 build_booklog.py
cp booklog_all.json ../../data/booklog_purchases.json
cd ../.. && python3 scripts/import_booklog.py --rebuild
```

## 중복 처리

두 단계로 정리합니다.

**1단계 — 같은 기록의 갈래 합치기 (`merge_logs`)**
`backdata` 와 `google_sites` 는 같은 구매 기록이 시간이 지나며 갈라진 것이라 `(연도, 제목)` 으로
합집합 병합합니다. Google Sites 쪽 제목은 `(개정판)`, `(세계문학전집 214)`, `[일서]` 같은
꼬리표·말머리가 잘려 있는 경우가 많아 접두사 비교까지 합니다. 다만 잘린 뒤가 권차뿐이면
(`정약용과 그의 형제들` vs `…2`) 다른 권으로 보고 병합하지 않습니다.
결과: backdata 1,211 + google_sites 전용 27 = 1,260건.

**2단계 — 같은 책 합치기 (`dedupe_books`)**
출처를 가리지 않고 `(제목, 대표 저자)` 가 같으면 한 권으로 봅니다. 같은 책을 종이책으로 샀다가
오디오북으로 다시 듣거나, eBook 판과 오디오북 판이 따로 잡히거나, 밀리 계정 두 곳에 모두 있는
경우가 많습니다. 72건이 이 단계에서 합쳐집니다.

- **가장 먼저 기록된 것**을 대표로 남깁니다. 연도가 뒤섞이지 않게 하기 위해서입니다.
- 비어 있는 칸(저자·출판사·ISBN·표지 등)은 다른 기록에서 채웁니다.
- **읽은 비율은 가장 많이 읽은 쪽**을 씁니다. eBook 81% + 오디오북 완독이면 완독으로 남깁니다.
- 대표와 연도·출처가 다른 기록은 비고에 `다시 읽음: 2025 교보문고` 처럼 적어 둡니다 (45건).
- 제목이 같아도 저자가 다르면 다른 책입니다 (`여름` — 이디스 워튼 / 알베르 까뮈).
  다만 `루이자 메이 올컷` vs `올콧` 처럼 표기만 다른 경우는 유사도 0.8 이상이면 같은 책으로 봅니다.

## 원본을 다시 수집하려면

- **Google Sites**: `https://sites.google.com/site/istandby4u2/booklog/{2010..2017}` 의 서버 응답 HTML에
  구매 내역 표가 이스케이프된 형태로 들어 있습니다. `&lt;table&gt; … &lt;/table&gt;` 블록을 언이스케이프해
  파싱하면 됩니다 (브라우저에서 innerText로는 읽히지 않습니다).
- **교보문고**: 로그인된 세션에서
  - 온라인 주문: `GET order.kyobobook.co.kr/api/comm/ord/v1/order/orderList`
    (`mmbrNum`, `startDate`, `endDate`, `pageIndex`, `pageSize`)
  - 매장 구매: `POST order.kyobobook.co.kr/api/comm/ord/v1/offline/offlineList`
    (JSON body: `startDate`, `endDate`, `page`, `pageUnit`, `slsRtgdDvsnCode`, `strAreaGrpCode`, `strRdpCode`, `cmdtName`)

  조회 기간은 **6개월 단위, 최대 5년**까지만 허용됩니다. 저자 정보는 주문 API에 없으므로
  상품 페이지에서 따로 가져옵니다 — 종이책은 `product.kyobobook.co.kr/detail/{saleCmdtid}` 의
  `productAuthorName`·`pubDate`, eBook·오디오북은
  `ebook-product.kyobobook.co.kr/dig/epd/ebook/{saleCmdtid}` 의 `<title>` (`제목 | 저자 | 출판사`).

## 밀리의 서재 · Audible 수집 방법

- **밀리의 서재**: `apis.millie.co.kr/v3/library/books/my/` 가 목록 API지만 CORS 때문에 직접 호출은
  막힙니다. 대신 `www.millie.co.kr/v4/library/books` 에서 `XMLHttpRequest.prototype.open` 을 후킹해
  페이지 자신의 응답을 모으고, 끝까지 스크롤해 전량을 받는 방식으로 수집했습니다.
  `read_category` 는 10=읽고 싶은 책, 20=읽는 중, 30=완독입니다.
- **Audible Japan**: `www.audible.co.jp/library/titles?pageSize=50` 의 DOM에서 읽습니다.
  `library/podcasts` 로 팟캐스트 ASIN을 따로 받아 도서에서 제외합니다.

## 알려진 공백

- **2019–2020년**: 어느 출처에도 없습니다. 직접 정리한 도서 DB가 2018년에서 끊기고, 교보문고는
  5년(2021-08~)까지만 조회되며, 밀리의 서재는 2022-11부터 시작합니다.
- **Audible 은 연도가 없습니다.** 구독(듣기 무제한)으로 이용해 주문 기록이 남지 않습니다 —
  주문·구매 내역 페이지가 `注文済みのタイトルはありません` 을 반환합니다. 연도 미지정으로 들어갑니다.
- 교보문고 매장(오프라인) 구매 내역은 조회 가능 기간 내 `totalRecords: 0` — 기록이 없습니다.
- 교보 데이터 중 사은품·sam 이용권과 반품완료 건은 제외했습니다.
- 밀리·Audible 은 '구매'가 아니라 구독으로 읽은 기록이라 `purchase_date` 에는 읽은 날(없으면
  서재에 담은 날)이 들어갑니다.
