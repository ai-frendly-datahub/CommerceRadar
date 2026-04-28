# 14. 고도화 데이터 소스 카탈로그

## 1. 데이터 소스 분류

| 영역 | 핵심 소스 | 목적 |
|---|---|---|
| 제조사 | 홈페이지, 제품 상세, 공장등록, 인증, 특허/상표 | 생산 가능성과 제품 스펙 파악 |
| 유통사 | 포트폴리오, 위치, 물류창고, 통관/무역 | 유통 가능 범위와 실행력 파악 |
| 판매사 | 판매 채널, 베스트셀러, 리뷰, 소셜 콘텐츠 | 판매 역량과 트렌드 적합성 파악 |
| 시장 | KOSIS, METI, 중국 NBS, 관세청, UN Comtrade | 국가·카테고리 수요 판단 |
| 트렌드 | 네이버 데이터랩, Rakuten, Google Trends, TikTok, 샤오홍수, 더우인 | 키워드·콘텐츠·소비 욕망 탐지 |
| 내부 | 미팅, 샘플, 테스트 판매, 계약, 재발주 | 플로머스 고유 해자 |

---

## 2. 제조사 데이터 소스

### 2.1 공식 홈페이지/제품 상세페이지

수집 항목:

```text
제품명, 상세 설명, 스펙, 성분/소재, 용량, 패키지, 이미지, 카탈로그 PDF, 인증, OEM/ODM, MOQ, 수출 경험
```

활용:

```text
제품-채널 적합도
제품-트렌드 적합도
인증/통관 리스크
판매 문장 추출
```

참고:
- Schema.org Product: https://schema.org/Product
- Google Product structured data: https://developers.google.com/search/docs/appearance/structured-data/product

### 2.2 한국 공장등록 데이터

활용:

```text
제조사 후보 발굴
생산품/업종 기준 분류
지역별 제조 클러스터 파악
```

### 2.3 인증/안전 데이터

예시:

```text
MFDS 화장품/원료/의약외품
Safety Korea KC 인증/리콜
KIPRIS 상표/특허
GS1 바코드/GEPIR
```

활용:

```text
제품 판매 가능성 검증
상표/IP 리스크 확인
정품성 확인
상세페이지 금지 표현 관리
```

---

## 3. 유통사 데이터 소스

### 3.1 홈페이지/포트폴리오

```text
취급 브랜드, 취급 카테고리, 납품 사례, B2B 문의, 물류센터, 지사, 영업 지역
```

### 3.2 위치/창고/물류

```text
물류창고업등록정보
Google Places
OpenStreetMap/Nominatim
Geoapify Places
```

활용:

```text
도쿄권/오사카권/수도권 등 유통 커버리지 추론
냉장/보세/일반 물류 가능성 판단
고중량/액체류/화장품 배송 리스크 판단
```

### 3.3 무역/통관

```text
관세청 수출입통계
일본 재무성 무역통계/e-Stat
중국 해관총서 통계
UN Comtrade
WTO Stats
```

활용:

```text
HS코드별 성장 품목
국가별 수출입 증가율
중국→한국, 한국→일본, 일본→중국 흐름 탐지
```

---

## 4. 판매사 데이터 소스

### 4.1 플랫폼 상점

```text
스마트스토어
쿠팡
Cafe24 자사몰
Shopify Store
Rakuten Shop
Amazon Storefront
BASE/STORES
샤오홍수/더우인 상점
```

수집 항목:

```text
베스트셀러, 가격대, 리뷰 수, 평점, 카테고리, 배송 조건, 상세페이지 톤, 반품 정책
```

### 4.2 소셜/콘텐츠 채널

```text
Instagram
TikTok
YouTube
X
Pinterest
샤오홍수
더우인
위챗 공식계정
LINE 공식계정
카카오톡 채널
```

수집 항목:

```text
콘텐츠 스타일, 게시 빈도, 댓글 키워드, 상품 태그, 라이브 이력, 광고 협업 이력
```

### 4.3 트렌드 도구

```text
네이버 데이터랩
Rakuten Item Search/Ranking API
Google Trends
TikTok Creative Center
Meta Ad Library
Douyin Index/Ocean Engine
샤오홍수 蒲公英/오픈플랫폼
```

참고:
- KOSIS OpenAPI는 JSON, SDMX, XML, XLS 등 형태로 통계정보를 제공한다: https://kosis.kr/serviceInfo/openAPIGuide.do
- Rakuten Ichiba Item Search API는 라쿠텐 이치바에 등록된 상품 데이터를 키워드, 상점, 장르 기준으로 조회할 수 있다: https://webservice.rakuten.co.jp/documentation/ichiba-item-search

---

## 5. 수집 주기

| 데이터 | 주기 | 이유 |
|---|---|---|
| 제품 상세/스펙 | 월 1회 | 제품 라인업 변화 |
| 판매사 베스트셀러 | 일/주 1회 | 트렌드 변화 빠름 |
| 리뷰/댓글 키워드 | 주 1회 | 소비자 언어 변화 |
| 공공 통계 | 월/분기 1회 | 발표 주기 기반 |
| 무역 데이터 | 월 1회 | HS코드 흐름 관찰 |
| 인증/리콜 | 주 1회 | 리스크 관리 |
| 내부 거래 결과 | 실시간/이벤트 기반 | 추천 정확도 핵심 |

---

## 6. 우선순위

### 1순위

```text
제조사 홈페이지 제품 상세
공장등록/사업자 상태
통신판매사업자
네이버 데이터랩
KOSIS 온라인쇼핑
관세청 수출입
Rakuten API
일본 법인번호
플로머스 내부 거래 데이터
```

### 2순위

```text
인증/리콜/IP/바코드
물류창고/위치 데이터
Cafe24/Shopify/Coupang 권한 기반 API
Amazon SP-API
KOTRA 시장뉴스/전시회
```

### 3순위

```text
샤오홍수/더우인 공식 연동
TikTok/Meta/Google Trends
중국 기업 검증 데이터
UN Comtrade/WTO/e-Stat 고도화
```
