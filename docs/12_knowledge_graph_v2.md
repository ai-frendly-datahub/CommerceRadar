# 12. 지식 그래프 v2 설계

## 1. 설계 목표

플로머스 지식 그래프는 업체 명단을 연결하는 그래프가 아니다. 목표는 **거래 가능성을 설명하는 그래프**다.

```text
업체를 연결한다 → 약함
상품·조건·채널·트렌드·결과를 연결한다 → 강함
```

---

## 2. 핵심 노드

| 노드 | 의미 | 예시 |
|---|---|---|
| Manufacturer | 제조사 | ABC코스메틱 |
| Product | 제품 | 노워시 퍼퓸 헤어오일 |
| ProductSpec | 제품 스펙 | 80ml, 펌프형, 향 지속 |
| Distributor | 유통사 | Tokyo Beauty Distribution |
| Seller | 판매사 | Tokyo Beauty Select |
| Portfolio | 포트폴리오 | 헤어·향·핸드크림 판매 이력 |
| Location | 위치 | Tokyo, Saitama warehouse |
| Channel | 채널 | Instagram, BASE, Rakuten, Xiaohongshu |
| Trend | 트렌드 | 향 지속, 손상모, 선물형 뷰티 |
| Keyword | 키워드 | fragrance, damaged hair |
| TradeCondition | 거래 조건 | MOQ, 공급가, 위탁 여부 |
| Evidence | 근거 | 제품 페이지, API, 미팅 메모 |
| Transaction | 거래 | 테스트 판매, 본계약, 재발주 |
| Risk | 리스크 | 인증, IP, 액체 배송 |

---

## 3. 핵심 관계

### 제조사/제품 관계

```text
Manufacturer -[PRODUCES]-> Product
Product -[HAS_SPEC]-> ProductSpec
Product -[HAS_KEYWORD]-> Keyword
Product -[MATCHES_TREND]-> Trend
Product -[REQUIRES_CERTIFICATION]-> Risk
Product -[SUITABLE_FOR_CHANNEL]-> Channel
```

### 유통사 관계

```text
Distributor -[HAS_PORTFOLIO]-> Portfolio
Distributor -[LOCATED_IN]-> Location
Distributor -[OPERATES_IN]-> Country
Distributor -[DISTRIBUTES_CATEGORY]-> Category
Distributor -[CAN_HANDLE]-> TradeCondition
Distributor -[SUPPORTS_CHANNEL]-> Channel
```

### 판매사 관계

```text
Seller -[HAS_PORTFOLIO]-> Portfolio
Seller -[SELLS_ON]-> Channel
Seller -[STRONG_IN]-> Category
Seller -[FOLLOWS_TREND]-> Trend
Seller -[TARGETS]-> CustomerSegment
Seller -[HAS_CONTENT_STYLE]-> ContentStyle
```

### 거래 관계

```text
Product -[TESTED_WITH]-> Seller
Manufacturer -[MATCHED_WITH]-> Distributor
Distributor -[FULFILLED_FOR]-> Seller
Transaction -[RESULTED_IN]-> Outcome
Transaction -[FAILED_BECAUSE]-> Risk
Transaction -[GENERATED_EVIDENCE]-> Evidence
```

---

## 4. 근거 중심 그래프

모든 관계는 반드시 근거를 가져야 한다.

```json
{
  "edge": "Product MATCHES_TREND Trend",
  "confidence": 0.76,
  "evidence_ids": ["ev_rakuten_ranking_2026_04", "ev_seller_review_keywords"],
  "created_at": "2026-04-28",
  "valid_until": "2026-07-28"
}
```

근거 유형:

| 근거 유형 | 신뢰도 기본값 |
|---|---:|
| 공개 웹페이지 | 0.35 |
| 플랫폼 공개 페이지 | 0.45 |
| 정부/공식 API | 0.75 |
| 업체 제출 자료 | 0.65 |
| 플로머스 검수 | 0.85 |
| 실제 테스트 거래 | 0.95 |
| 재발주/정산 완료 | 1.00 |

---

## 5. 시간성을 가진 관계

유통 데이터는 시간이 지나면 썩는다. 따라서 관계는 시간 필드를 가져야 한다.

```text
created_at
updated_at
observed_at
verified_at
valid_until
staleness_score
```

예시:

```text
Tokyo Beauty Select -[STRONG_IN]-> fragrance
근거: 2026년 4월 포트폴리오/리뷰 키워드 수집
유효 기간: 90일
```

---

## 6. 부정 근거도 저장한다

실패 데이터는 성공 데이터만큼 중요하다.

```text
FAILED_BECAUSE: MOQ 불일치
FAILED_BECAUSE: 가격 저항
FAILED_BECAUSE: 판매사 물류 역량 부족
FAILED_BECAUSE: 인증 자료 미비
FAILED_BECAUSE: 상세페이지 표현 리스크
```

부정 근거는 다음 추천에서 리스크 감점으로 반영된다.

---

## 7. 그래프 검색 패턴

### 패턴 A: 제품에서 판매사 찾기

```text
Product
→ Category
→ Trend
→ Seller Portfolio
→ Seller Channel
→ Past Transaction
```

### 패턴 B: 제조사에서 국가 추천

```text
Manufacturer
→ Product Specs
→ HS Code / Category
→ Market Demand
→ Similar Platform Products
→ Country Fit
```

### 패턴 C: 유통사 보완 파트너 찾기

```text
Distributor
→ Portfolio
→ Weakness
→ Seller Capability
→ Complementary Match
```

---

## 8. GraphRAG 적용 방식

GraphRAG는 복잡한 정보에 대해 지식 그래프를 활용해 질의응답 성능을 높이는 접근으로 설명된다. 플로머스에서는 문서에서 엔티티와 관계를 추출하고, 그래프 탐색과 벡터 검색을 결합해 조합 추천 근거를 만든다.

참고:
- Microsoft GraphRAG: https://microsoft.github.io/graphrag/
- Microsoft Research GraphRAG: https://www.microsoft.com/en-us/research/project/graphrag/

---

## 9. MVP 그래프 범위

```text
제조사 100개
제품 500개
유통사 100개
판매사 100개
트렌드 300개
근거 2,000개
조합 카드 100개
실제 테스트 거래 10개
```

MVP의 목표는 전체 시장을 다 담는 것이 아니라, **조합 추천이 근거와 함께 나오는 상태**를 만드는 것이다.
