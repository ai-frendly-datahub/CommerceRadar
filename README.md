# Flomers Commerce Knowledge Graph

플로머스가 한·중·일 제조사, 유통사, 판매사를 맥락 기반으로 연결하기 위한 **B2B 커머스 지식망 프로젝트**입니다.

이 프로젝트의 목표는 단순 업체 DB가 아니라 다음 질문에 답하는 검색·추천 엔진을 만드는 것입니다.

> 이 제품을 누가 만들 수 있고, 누가 유통할 수 있고, 누가 팔 수 있으며, 지금 어떤 트렌드로 팔아야 하는가?

패키지 버전은 `pyproject.toml`의 `0.2.0`입니다. `CHANGELOG.md`의 `v0.2.1`은 대시보드용 리포트 산출을 더합니다. 스케줄 수집은 [9. Radar 수집 파이프라인](#9-radar-수집-파이프라인)입니다.

---

## 1. 핵심 개념

플로머스의 가치는 직접 상품을 파는 데서 끝나지 않습니다. 핵심은 제조사·유통사·판매사 사이에서 **거래가 성사될 가능성이 높은 조합**을 찾아내고, 그 조합을 테스트 거래와 반복 발주로 연결하는 것입니다.

```text
제조사 제품 상세/스펙
→ 유통사 포트폴리오/위치/물류
→ 판매사 포트폴리오/트렌드/채널
→ 국가·카테고리·플랫폼 수요 데이터
→ 조합 추천
→ 30일 테스트 거래
→ 결과 데이터 반영
→ 매칭 정확도 개선
```

---

## 2. 저장소 구성

```text
CommerceRadar/
├── README.md
├── AGENTS.md
├── CHANGELOG.md
├── Makefile
├── main.py                          # 일일 수집·리포트 진입점
├── pyproject.toml
├── LICENSE
├── .gitignore
├── docs/
│   ├── 01_business_value.md
│   ├── 02_data_source_map.md
│   ├── 03_ontology_design.md
│   ├── 04_contextual_search_design.md
│   ├── 05_matching_score.md
│   ├── 06_data_pipeline.md
│   ├── 07_mvp_roadmap.md
│   ├── 08_compliance_and_governance.md
│   ├── 09_operating_playbook.md
│   ├── 10_discussion_summary.md
│   ├── 11_advanced_analysis_framework.md
│   ├── 12_knowledge_graph_v2.md
│   ├── 13_retrieval_and_ranking_architecture.md
│   ├── 14_data_source_catalog_advanced.md
│   ├── 15_entity_resolution_and_quality.md
│   ├── 16_gtm_and_monetization.md
│   ├── 17_experiment_design.md
│   ├── 18_product_requirements.md
│   ├── 19_risk_register.md
│   └── 20_metrics_tree.md
├── config/
│   ├── sources.yaml                 # 수집기가 읽는 출처 스위치
│   ├── data_sources.yaml            # 전략 카탈로그 (수집 루프가 읽지 않음)
│   ├── categories/commerce.yaml
│   ├── advanced_scoring.yaml
│   ├── data_quality.yaml
│   ├── ontology.yaml
│   ├── retrieval.yaml
│   └── scoring.yaml
├── commerceradar/                   # 수집, 날짜별 저장, 리포트, 품질
├── src/flomers_kg/                  # 지식망 모델, 점수, 검색, 샘플 리포트
├── scripts/
│   ├── build_sample_graph.py
│   ├── run_sample_search.py
│   ├── run_advanced_analysis.py
│   ├── build_report_artifacts.py
│   └── check_quality.py
├── schemas/
├── data/samples/                    # 테스트·조합 카드용 시드. 수집 기사가 아님
├── data/raw/<YYYY-MM-DD>/           # UTC 날짜 수집 로그
├── data/daily/                      # --snapshot-db 일 때 DB 스냅샷 루트
├── reports/                         # HTML, summary JSON, index.html
├── tests/
└── .github/workflows/
    ├── ci.yml
    ├── pr-checks.yml
    ├── release.yml
    ├── radar-crawler.yml
    └── health-check.yml
```

`schemas/`와 `data/samples/`의 파일 이름은 아래와 같다.

```text
schemas/
├── combo_card.schema.json
├── manufacturer.schema.json
├── distributor.schema.json
├── seller.schema.json
├── product.schema.json
├── trend.schema.json
├── match_candidate.schema.json
├── evidence.schema.json
└── transaction_result.schema.json

data/samples/
├── manufacturers.jsonl
├── distributors.jsonl
├── sellers.jsonl
├── products.jsonl
├── trends.jsonl
├── evidence_records.jsonl
└── transactions.jsonl
```

`src/flomers_kg/`에서 확인된 모듈: `models.py`, `scoring.py`, `advanced_scoring.py`, `graph.py`, `search.py`, `query_planner.py`, `data_quality.py`, `combo_card.py`, `reporting.py`, `extraction_templates.py`, `sample_pipeline.py`.

`commerceradar/`에서 확인된 모듈: `collector.py`, `config_loader.py`, `date_storage.py`, `storage.py`, `reporter.py`, `quality_report.py`, `analyzer.py`, `models.py`.

---

## 3. 빠른 실행

Python `>=3.11`이 필요하다. 런타임 의존성에는 `radar-core`(`ai-frendly-datahub/radar-core`의 `main`)가 포함된다. dev extra는 pytest다.

샘플 검색과 리포트, 테스트는 Makefile·CI와 같은 설치를 쓴다.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python scripts/build_report_artifacts.py
python scripts/run_sample_search.py
```

`make install`은 `pip install -e .[dev]`이다. `make test`는 `pytest -q`, `make sample`은 `scripts/run_sample_search.py`, `make graph`는 `scripts/build_sample_graph.py`, `make report`는 `scripts/build_report_artifacts.py`이다. CI(`.github/workflows/ci.yml`)도 Python 3.11에서 `pip install -e .[dev]` 다음 `pytest -q`를 실행한다.

`pip install -e .`는 pytest 없이 런타임 의존성만 설치한다. 정기 수집 명령은 9절이다.

`scripts/run_sample_search.py`가 고정으로 출력하는 첫 줄은 아래다.

```text
검색어: 일본에서 향·헤어 트렌드에 맞는 제조사-유통사-판매사 조합
```

이어서 추천 조합, 제품, 점수와 `recommendation_level`, 추천 근거, 리스크, 다음 액션을 여러 줄로 출력한다. 점수 숫자는 소스에 고정되어 있지 않다. 이 질의의 샘플 레코드에는 ABC코스메틱, 노워시 퍼퓸 헤어오일, Tokyo Beauty Distribution, Tokyo Beauty Select가 있다 (`data/samples/`).

고도화 샘플:

```bash
python scripts/run_advanced_analysis.py
```

이 스크립트는 질의 계획, 고도화 점수 분해, 조합 카드 마크다운을 출력한다.

워크스페이스에 형제 디렉터리 `radar-core`가 있으면 `main.py`와 `scripts/check_quality.py`가 그 경로를 `sys.path` 앞에 넣는다. 없으면 설치된 `radar-core` 패키지를 쓴다.

---

## 4. 데이터 수집 기준

이 절은 지식망에 남길 필드 기준이다. 스케줄 수집기가 켜 둔 출처는 `config/sources.yaml`과 9절이 기준이다. 제조사 홈페이지(`manufacturer_websites`)는 단일 공개 RSS가 없고 사이트별 robots.txt를 우회하지 않도록 `enabled: false`다. `data/samples/`는 조합 카드와 테스트용 시드이며 수집 기사가 아니다.

### 제조사

제조사는 홈페이지의 제품 상세페이지와 스펙을 중심으로 수집합니다.

```text
제품명, 카테고리, 상세 설명, 성분/소재, 용량/중량/사이즈, 패키지, 인증, OEM/ODM, MOQ, 리드타임, 이미지, 카탈로그, 수출 경험
```

### 유통사

유통사는 포트폴리오와 위치를 중심으로 수집합니다.

```text
취급 브랜드, 취급 카테고리, 창고 위치, 영업 지역, 수입/통관 가능 여부, 사입/위탁/총판 가능 여부, 온라인/오프라인 채널
```

### 판매사

판매사는 포트폴리오와 트렌드 적합성을 중심으로 수집합니다.

```text
운영 채널, 베스트셀러, 가격대, 리뷰, 콘텐츠 스타일, 고객층, 트렌드 키워드, 라이브 가능 여부, 광고 집행력, 위탁/사입 가능 여부
```

---

## 5. 검색 결과의 목표 형식

플로머스 검색은 단순 리스트가 아니라 **조합 카드**를 반환해야 합니다.

```text
조합 카드
- 제조사
- 제품
- 유통사
- 판매사
- 대상 국가
- 대상 채널
- 매칭 점수
- 추천 근거
- 리스크
- 다음 액션
```

---

## 6. 핵심 원칙

```text
업체를 검색하지 말고, 거래 가능성을 검색한다.
데이터를 쌓지 말고, 거래 판단을 축적한다.
공개 데이터는 입구이고, 실제 거래 결과 데이터가 해자다.
```

---

## 7. 문서 시작점

- [사업 가치 설계](docs/01_business_value.md)
- [데이터 소스 맵](docs/02_data_source_map.md)
- [지식 그래프 온톨로지](docs/03_ontology_design.md)
- [맥락 기반 검색 설계](docs/04_contextual_search_design.md)
- [매칭 점수 모델](docs/05_matching_score.md)
- [데이터 파이프라인](docs/06_data_pipeline.md)
- [MVP 로드맵](docs/07_mvp_roadmap.md)
- [컴플라이언스와 거버넌스](docs/08_compliance_and_governance.md)
- [운영 플레이북](docs/09_operating_playbook.md)

---

## 8. v0.2 고도화 내용

이번 버전은 기존 정리본을 **분석형 실행 저장소**로 확장했습니다.

```text
분석 프레임워크 고도화
지식 그래프 v2 설계
맥락 검색·랭킹 아키텍처
고도화 데이터 소스 카탈로그
엔티티 정규화/데이터 품질 정책
GTM·수익화 전략
30일 테스트 거래 실험 설계
MVP PRD
리스크 레지스터
지표 트리
고도화 점수 모델과 조합 카드 생성 코드
```

추가 문서:

- [고도화 분석 프레임워크](docs/11_advanced_analysis_framework.md)
- [지식 그래프 v2 설계](docs/12_knowledge_graph_v2.md)
- [맥락 검색·랭킹 아키텍처](docs/13_retrieval_and_ranking_architecture.md)
- [고도화 데이터 소스 카탈로그](docs/14_data_source_catalog_advanced.md)
- [엔티티 정규화와 데이터 품질](docs/15_entity_resolution_and_quality.md)
- [GTM과 수익화 전략](docs/16_gtm_and_monetization.md)
- [테스트 거래 실험 설계](docs/17_experiment_design.md)
- [MVP 제품 요구사항 PRD](docs/18_product_requirements.md)
- [리스크 레지스터](docs/19_risk_register.md)
- [지표 트리](docs/20_metrics_tree.md)

`config/data_sources.yaml`과 `docs/14_data_source_catalog_advanced.md`는 수집 전략 카탈로그다. 매일 도는 수집기가 읽고 켜고 끄는 목록은 `config/sources.yaml`이다.

---

## 9. Radar 수집 파이프라인

### 실행

로컬에서 카테고리 `commerce` 수집과 리포트를 한 번에 돌린다.

```bash
python main.py --category commerce
```

GitHub Actions `Radar Crawler (Commerce)` (`.github/workflows/radar-crawler.yml`)는 설치 후 아래를 실행한다.

```bash
python main.py --category commerce --snapshot-db --keep-days 90 --keep-raw-days 90 --keep-report-days 90
```

`--snapshot-db`는 `data/radar_data.duckdb`가 있을 때 그 파일을 `data/daily/` 아래로 복사한다. 파일이 없으면 스냅샷을 만들지 않는다. `--keep-days`는 DB 스냅샷 보존 일수다. `main.py`의 세 keep 기본값은 모두 90이다. `commerceradar/date_storage.py`의 `keep_snapshot_days` 기본값은 30이지만, `main.py`가 90을 넘긴다.

같은 워크플로는 이어서 `python scripts/check_quality.py`를 실행한다 (실패해도 잡 자체는 계속). `Health Check` 워크플로는 `python main.py --category commerce`로 `reports/index.html`이 생기는지 본 다음 `pytest tests/unit -q`를 실행한다. 헬스체크는 `--snapshot-db`를 넘기지 않는다.

워크플로 설치는 `radar-core` git URL을 설치한 뒤 `pip install -e .[dev]`이다.

### 활성 수집 소스

수집기는 `config/sources.yaml`의 `sources` 목록만 가져온다. `enabled: false`이거나 `id`가 `sample_`로 시작하거나 `type`이 `sample`로 시작하면 HTTP 요청을 하지 않는다. `config/categories/commerce.yaml`의 샘플 출처(`commerce_kg_trends`, `commerce_kg_manufacturers`)는 둘 다 `enabled: false`이고, 수집 루프의 입력이 아니다.

`enabled: true` (4개):

| id | type | 수집 URL |
| --- | --- | --- |
| `korea_factory_registration` | `html_meta` | `https://www.data.go.kr/data/15105482/fileData.do` |
| `korea_ecommerce_business_registration` | `html_meta` | `https://www.data.go.kr/data/15083251/fileData.do` |
| `kosis` | `rss` | `https://kosis.kr/rss/notice_rss.jsp` |
| `customs_trade_statistics` | `rss` | `https://www.customs.go.kr/kcs/selectBoardRss.do?mi=15265&bbsId=1362` |

공장등록·통신판매는 공개 파일데이터 페이지의 메타만 읽고, CSV 원문과 인증 API는 받지 않는다. KOSIS는 공식 공지 RSS만 사용하고 통계표 API 키는 호출하지 않는다. 관세청은 보도자료 RSS만 사용하고 UN Comtrade 미리보기 API는 쓰지 않는다. robots.txt 차단, HTTP 401/403, Cloudflare 챌린지는 실패로 기록하고 건너뛴다.

`enabled: false` (6개): `manufacturer_websites`, `naver_datalab`, `rakuten_web_service`, `flomers_internal_transactions`, `xiaohongshu_open_platform`, `douyin_open_platform`.

2026-10-20 수집분(`data/raw/2026-10-20/source_results.json`)은 활성 4개 중 3개를 가져왔다. 공장등록 1건, 통신판매 1건, 관세청 RSS 20건이다. `kosis`는 그 실행에서 `blocked`(robots.txt 연결 시간 초과)이고 0건이다.

### 샘플 시드

`data/samples/*.jsonl`은 테스트와 조합 카드용이다. `commerceradar/collector.py`는 이 디렉터리를 기사로 만들지 않는다. `materialize_kg_raw_snapshot`은 샘플 JSONL을 `data/raw/`로 복사하지 않고 `None`을 반환한다.

2026-10-19 raw에는 샘플 JSONL 사본(`manufacturers.jsonl`, `distributors.jsonl`, `sellers.jsonl`, `products.jsonl`, `trends.jsonl`, `evidence_records.jsonl`, `transactions.jsonl`)과 샘플 트렌드 기사 로그 `commerce_kg_trends.jsonl`이 있다. 2026-10-20 raw에서 확인된 파일은 `source_results.json`과 `commerce_sources.jsonl`이다. 같은 날짜에서 위 샘플 파일명과 `commerce_kg_trends.jsonl`은 없었다. 두 디렉터리의 그 밖 파일명은 전체 목록을 열지 않아 [미확인]이다.

`commerceradar/quality_report.py`는 `data/raw/*/commerce_kg_trends.jsonl` 중 정렬상 마지막 파일을 품질 검사에 쓴다. 10/20에는 그 파일이 없으므로, 10/19 샘플 트렌드 로그가 남아 있는 동안 품질 검사가 그 파일을 볼 수 있다.

### 스케줄

| 워크플로 | cron (UTC) | KST (UTC+9) | 그 외 |
| --- | --- | --- | --- |
| `radar-crawler.yml` Radar Crawler (Commerce) | `30 18 * * *` (18:30 UTC) | 03:30, 다음 달력일 | `workflow_dispatch` |
| `health-check.yml` Health Check | `0 6 * * *` (06:00 UTC) | 15:00, 같은 달력일 | `workflow_dispatch`. `TZ`는 지정하지 않음 |

크롤러 파일의 `TZ: Asia/Seoul`은 GitHub cron 시계를 바꾸지 않는다. cron은 UTC다.

raw 디렉터리 이름은 UTC 날짜다 (`datetime.now(UTC)`). 리포트 파일의 날짜는 `date.today()`이다. 크롤러는 `TZ=Asia/Seoul`이므로 그 잡의 리포트 달력은 KST다. 18:30 UTC 실행이면 raw 날짜와 리포트 날짜가 하루 어긋난다. 관측값: raw는 `data/raw/2026-10-20/`, `reports/index.html`의 최신 리포트 날짜는 2026-10-21, `generated_at`은 `2026-10-20T21:45:43+00:00`이다.

### 데이터 경로

| 경로 | 내용 |
| --- | --- |
| `data/raw/<UTC YYYY-MM-DD>/source_results.json` | 출처별 status, count |
| `data/raw/<UTC YYYY-MM-DD>/commerce_sources.jsonl` | 수집 기사. RawLogger `source_name`이 `commerce_sources` |
| `data/radar_data.duckdb` | 컴팩트 대상 DB. 파일이 있을 때만 스냅샷 |
| `data/daily/` | `--snapshot-db` 스냅샷 루트. 내부 파일명은 `radar-core`의 `snapshot_database`가 정함 |
| `reports/commerce_YYYYMMDD.html` | 당일 HTML 리포트 |
| `reports/commerce_YYYYMMDD_summary.json` | 카드 본문을 뺀 summary |
| `reports/index.html` | 최신 리포트로 가는 인덱스 |
| `reports/commerce_quality.json` | `write_quality_report`가 쓰는 품질 JSON |

`config/categories/commerce.yaml`의 `dated_freshness_report_pattern`은 `reports/commerce_YYYYMMDD_quality.json`이다. 현재 `write_quality_report`는 그 날짜 파일을 쓰지 않고 `reports/commerce_quality.json`만 쓴다.

`.gitignore`는 `/data/raw/`와 `/data/processed/`를 무시한다. 크롤러의 auto-commit은 `data/`와 `reports/`를 `-f`로 넣고 `data/search_index.db*`만 제외한다. raw·리포트·스냅샷 파일 보존 일수는 워크플로 기준 90일이다. 리포트 아티팩트 업로드 보존은 30일이다 (`retention-days: 30`). 이 값은 git에 남는 기간과 별개다.

완료 검사는 `data/raw/<UTC 또는 KST 날짜>`, `data/snapshots/<날짜>`, `data/daily/` 바로 아래의 날짜 접두 파일을 본다. 저장 코드가 스냅샷을 두는 루트는 `data/daily/`이다. `data/snapshots/`는 이 저장 코드가 쓰지 않는다.

### GitHub Pages

크롤러는 `reports/`를 `gh-pages` 브랜치에 푸시한다 (`peaceiris/actions-gh-pages@v4`, `publish_dir: ./reports`). 인증은 Actions의 `GITHUB_TOKEN` 시크릿 참조다. 토큰 값은 저장소 파일에 없다.

공개 Pages URL은 워크플로, `CNAME`, README에서 확인하지 못했다. Pages URL: [미확인].

2026-10-21 확인 시 `gh-pages` 브랜치는 있지만 저장소 Pages 설정은 꺼져 있었다(GitHub API `has_pages: false`). 웹으로 공개하려면 저장소 Settings → Pages에서 `gh-pages` 브랜치를 게시 소스로 지정해야 한다.
