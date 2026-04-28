# 03. 지식 그래프 온톨로지 설계

## 1. 설계 목표

플로머스 지식망은 업체 목록을 저장하는 DB가 아니라 **거래 가능성을 추론하는 연결 구조**여야 한다.

```text
제조사 제품 스펙
→ 상품 카테고리
→ 국가별 수요
→ 유통사 포트폴리오/위치
→ 판매사 포트폴리오/트렌드
→ 매칭 후보
→ 거래 결과
```

---

## 2. 핵심 노드

| 노드 | 의미 |
|---|---|
| Manufacturer | 제조사 |
| Product | 제품 |
| ProductSpec | 제품 스펙 |
| Distributor | 유통사 |
| Seller | 판매사 |
| Portfolio | 포트폴리오 |
| Location | 위치 |
| Channel | 판매 채널 |
| Platform | 플랫폼 |
| Trend | 트렌드 |
| Keyword | 키워드 |
| Category | 카테고리 |
| Country | 국가 |
| TradeCondition | 거래 조건 |
| Transaction | 거래 결과 |
| Risk | 리스크 |
| SourceDocument | 원천 문서 |

---

## 3. 제조사 관계

```text
Manufacturer -[PRODUCES]-> Product
Product -[HAS_SPEC]-> ProductSpec
Product -[BELONGS_TO]-> Category
Product -[HAS_KEYWORD]-> Keyword
Product -[MATCHES_TREND]-> Trend
Product -[REQUIRES_CERTIFICATION]-> Risk
Product -[SUITABLE_FOR]-> Country
Product -[SUITABLE_FOR_CHANNEL]-> Channel
```

예시:

```text
ABC코스메틱 -[PRODUCES]-> 노워시 퍼퓸 헤어오일
노워시 퍼퓸 헤어오일 -[HAS_SPEC]-> 80ml / 펌프형 / 향 지속 / 손상모
노워시 퍼퓸 헤어오일 -[MATCHES_TREND]-> 일본 향 제품 선물 트렌드
```

---

## 4. 유통사 관계

```text
Distributor -[HAS_PORTFOLIO]-> Portfolio
Distributor -[LOCATED_IN]-> Location
Distributor -[OPERATES_IN]-> Country
Distributor -[DISTRIBUTES_CATEGORY]-> Category
Distributor -[HANDLES_CHANNEL]-> Channel
Distributor -[CAN_HANDLE]-> TradeCondition
Distributor -[GOOD_FOR]-> ProductType
```

예시:

```text
Tokyo Beauty Distribution -[LOCATED_IN]-> Tokyo
Tokyo Beauty Distribution -[DISTRIBUTES_CATEGORY]-> Haircare
Tokyo Beauty Distribution -[CAN_HANDLE]-> Consignment
```

---

## 5. 판매사 관계

```text
Seller -[HAS_PORTFOLIO]-> Portfolio
Seller -[SELLS_ON]-> Channel
Seller -[STRONG_IN]-> Category
Seller -[TARGETS]-> CustomerSegment
Seller -[FOLLOWS_TREND]-> Trend
Seller -[HAS_CONTENT_STYLE]-> ContentStyle
Seller -[GOOD_FOR]-> ProductType
Seller -[WEAK_IN]-> Capability
```

예시:

```text
Tokyo Beauty Select -[SELLS_ON]-> Instagram / BASE
Tokyo Beauty Select -[STRONG_IN]-> Haircare / Fragrance
Tokyo Beauty Select -[FOLLOWS_TREND]-> Giftable mini beauty
```

---

## 6. 거래 관계

```text
Product -[MATCHED_WITH]-> Seller
Manufacturer -[MATCHED_WITH]-> Distributor
Distributor -[CONNECTED_TO]-> Seller
MatchCandidate -[TESTED_WITH]-> Transaction
Transaction -[CONVERTED_TO_CONTRACT]-> Contract
Transaction -[FAILED_BECAUSE]-> Risk
Transaction -[GENERATED_REORDER]-> Reorder
```

---

## 7. 시간·근거 메타데이터

모든 노드와 관계는 다음 메타데이터를 가진다.

```text
source_id
source_url
source_type
collected_at
verified_at
confidence_level
valid_until
created_by
updated_by
```

유통 데이터는 시간이 지나면 가치가 낮아지므로 `valid_until`과 `verified_at`은 필수다.
