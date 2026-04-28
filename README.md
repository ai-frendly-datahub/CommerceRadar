# Flomers Commerce Knowledge Graph

플로머스가 한·중·일 제조사, 유통사, 판매사를 맥락 기반으로 연결하기 위한 **B2B 커머스 지식망 프로젝트**입니다.

이 프로젝트의 목표는 단순 업체 DB가 아니라 다음 질문에 답하는 검색·추천 엔진을 만드는 것입니다.

> 이 제품을 누가 만들 수 있고, 누가 유통할 수 있고, 누가 팔 수 있으며, 지금 어떤 트렌드로 팔아야 하는가?

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
├── docs/
│   ├── 01_business_value.md
│   ├── 02_data_source_map.md
│   ├── 03_ontology_design.md
│   ├── 04_contextual_search_design.md
│   ├── 05_matching_score.md
│   ├── 06_data_pipeline.md
│   ├── 07_mvp_roadmap.md
│   ├── 08_compliance_and_governance.md
│   └── 09_operating_playbook.md
├── config/
│   ├── advanced_scoring.yaml
│   ├── data_quality.yaml
│   ├── ontology.yaml
│   ├── data_sources.yaml
│   ├── retrieval.yaml
│   ├── scoring.yaml
│   └── sources.yaml
├── reports/
├── schemas/
│   ├── combo_card.schema.json
│   ├── manufacturer.schema.json
│   ├── distributor.schema.json
│   ├── seller.schema.json
│   ├── product.schema.json
│   ├── trend.schema.json
│   ├── match_candidate.schema.json
│   ├── evidence.schema.json
│   └── transaction_result.schema.json
├── src/flomers_kg/
│   ├── models.py
│   ├── scoring.py
│   ├── graph.py
│   ├── search.py
│   ├── reporting.py
│   ├── extraction_templates.py
│   └── sample_pipeline.py
├── scripts/
│   ├── build_sample_graph.py
│   ├── run_sample_search.py
│   ├── run_advanced_analysis.py
│   └── build_report_artifacts.py
├── data/samples/
│   ├── manufacturers.jsonl
│   ├── distributors.jsonl
│   ├── sellers.jsonl
│   ├── products.jsonl
│   ├── trends.jsonl
│   ├── evidence_records.jsonl
│   └── transactions.jsonl
├── tests/
│   ├── test_scoring.py
│   └── test_graph.py
├── .github/workflows/ci.yml
├── .gitignore
├── LICENSE
└── pyproject.toml
```

---

## 3. 빠른 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python scripts/build_report_artifacts.py
python scripts/run_sample_search.py
```

예상 출력:

```text
검색어: 일본에서 향·헤어 트렌드에 맞는 제조사-유통사-판매사 조합
추천 조합 1: ABC코스메틱 × Tokyo Beauty Distribution × Tokyo Beauty Select
점수: 82
추천 액션: 샘플 20개 발송 → 일본어 상세페이지 제작 → BASE 30일 위탁 테스트
```

---

## 4. 데이터 수집 기준

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

고도화 샘플 실행:

```bash
python scripts/run_advanced_analysis.py
```

이 스크립트는 질의 계획, 고도화 점수 분해, 조합 카드 마크다운을 출력합니다.
