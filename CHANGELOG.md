# CHANGELOG

## v0.2.1 - 워크스페이스 대시보드 리포트

### Added

- Dashboard-readable `commerce_YYYYMMDD_summary.json`, HTML report, and `reports/index.html` generation.
- Report builder module `src/flomers_kg/reporting.py`.
- Report artifact command `scripts/build_report_artifacts.py` and Makefile `report` target.

### Verified

- `python3 -m pytest -q`
- `python3 scripts/build_report_artifacts.py`

## v0.2.0 - 분석 고도화

### Added

- 고도화 분석 프레임워크 문서
- 지식 그래프 v2 설계 문서
- 맥락 검색·랭킹 아키텍처 문서
- 고도화 데이터 소스 카탈로그
- 엔티티 정규화와 데이터 품질 정책
- GTM과 수익화 전략
- 테스트 거래 실험 설계
- MVP PRD
- 리스크 레지스터
- 지표 트리
- Evidence/Transaction/ComboCard 스키마
- 고도화 점수 모델 `advanced_scoring.py`
- 질의 계획기 `query_planner.py`
- 데이터 품질 점수 `data_quality.py`
- 조합 카드 렌더러 `combo_card.py`
- 고도화 샘플 실행 스크립트 `run_advanced_analysis.py`

### Changed

- README에 v0.2 고도화 문서와 실행법 추가
- pyproject 버전 0.2.0 반영

### Verified

- `/usr/bin/python3` + `PYTHONPATH=src` 기준 샘플 실행 확인
- 기존 테스트 함수와 신규 테스트 함수 수동 실행 확인
