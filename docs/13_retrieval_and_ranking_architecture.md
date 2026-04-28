# 13. 맥락 검색·랭킹 아키텍처

## 1. 검색의 목표

플로머스 검색은 문서를 찾는 검색이 아니라 **거래 조합을 찾는 검색**이다.

```text
입력: “일본에서 향·헤어 트렌드에 맞는 한국 제조사와 판매사 조합 찾아줘”
출력: 제조사 × 제품 × 유통사 × 판매사 조합 카드 + 근거 + 리스크 + 다음 액션
```

---

## 2. 4중 검색 구조

| 검색 방식 | 역할 | 예시 |
|---|---|---|
| Keyword Search | 정확 이름/코드 검색 | 업체명, 사업자번호, 제품명 |
| Vector Search | 의미 유사도 검색 | “향 오래가는 머리 제품” → 퍼퓸 헤어오일 |
| Graph Search | 관계 탐색 | 제품→트렌드→판매사→거래 결과 |
| Evidence Search | 근거 추적 | 제품 페이지, 미팅 메모, 판매 결과 |

단일 검색 방식으로는 부족하다. 키워드는 정확하지만 맥락이 약하고, 벡터는 의미는 강하지만 근거 추적이 약하며, 그래프는 관계는 강하지만 원문 근거가 필요하다.

---

## 3. 질의 분류

검색 요청은 먼저 의도별로 분류한다.

| 의도 | 예시 | 주요 검색 경로 |
|---|---|---|
| 업체 찾기 | 일본 뷰티 유통사 찾아줘 | Distributor/Seller + Portfolio |
| 제품 판단 | 이 제품 중국 샤오홍수에 맞아? | Product + Trend + Platform |
| 조합 추천 | 제조사-유통사-판매사 조합 짜줘 | Product + Distributor + Seller + Score |
| 실패 분석 | 왜 본계약 안 됐지? | Transaction + Risk + Evidence |
| 기회 발견 | 일본 틈새 카테고리 찾아줘 | Trend + Market + Competition |

---

## 4. 검색 파이프라인

```text
1. Query Understanding
   - 국가, 카테고리, 채널, 거래 목적, 제약조건 추출

2. Candidate Retrieval
   - 제품 후보
   - 제조사 후보
   - 유통사 후보
   - 판매사 후보
   - 트렌드 후보

3. Graph Expansion
   - 제품→키워드→트렌드
   - 유통사→포트폴리오→위치
   - 판매사→포트폴리오→리뷰 키워드
   - 과거 거래→성공/실패 근거

4. Scoring
   - 제품 적합도
   - 유통 적합도
   - 판매 적합도
   - 트렌드 적합도
   - 경제성
   - 리스크
   - 근거 신뢰도

5. Evidence Assembly
   - 각 추천 근거의 출처를 묶음

6. Response Generation
   - 조합 카드
   - 추천 이유
   - 리스크
   - 다음 액션
```

---

## 5. 랭킹 공식

```text
Final Rank Score =
0.18 × Product Fit
+ 0.15 × Distributor Fit
+ 0.15 × Seller Fit
+ 0.14 × Trend Fit
+ 0.12 × Market Potential
+ 0.10 × Economics
+ 0.08 × Execution Feasibility
+ 0.08 × Evidence Confidence
- Risk Penalty
- Staleness Penalty
```

고도화된 점수는 단순 매칭 점수와 달리 **근거 신뢰도와 최신성**을 반영한다.

---

## 6. 검색 결과 카드

```yaml
combo_card:
  title: "ABC코스메틱 × Tokyo Beauty Distribution × Tokyo Beauty Select"
  product: "노워시 퍼퓸 헤어오일"
  target_country: "JP"
  target_channels: ["Instagram", "BASE"]
  score: 92.1
  recommendation: "강력 추천"
  reasons:
    - "제품 스펙이 향·손상모 트렌드와 일치"
    - "유통사가 도쿄권 뷰티 소량 유통 포트폴리오 보유"
    - "판매사가 향·헤어 제품 콘텐츠 경험 보유"
  risks:
    - "액체류 배송 조건 확인 필요"
    - "일본어 성분 표기 필요"
  next_actions:
    - "샘플 20개 발송"
    - "KOC 5명 리뷰 테스트"
    - "BASE 30일 위탁 테스트"
  evidence:
    - "제품 상세페이지"
    - "유통사 포트폴리오 페이지"
    - "판매사 리뷰 키워드"
```

---

## 7. 근거 없는 답변 금지

검색 결과는 반드시 출처 유형과 신뢰도를 포함해야 한다.

```text
근거가 없는 추천 = 제외
근거가 약한 추천 = 조건부 테스트
실제 거래 결과가 있는 추천 = 우선 노출
```

---

## 8. 운영자 피드백 루프

검색 결과에는 운영자가 피드백을 남길 수 있어야 한다.

```text
적합함
부분 적합
부적합
미팅 진행
샘플 발송
거래 성사
거래 실패
재발주 발생
```

이 피드백은 다음 랭킹에 반영된다.
