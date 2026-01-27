## Step-1: Domain과 Scope 결정

### 1.1 기본 정의

| 항목 | 내용 |
| --- | --- |
| 도메인 | 3GPP RAN1 회의 문서 (Tdoc) |
| 용도 | 표준화 엔지니어 업무 지원 |
| 사용자 | 표준화 엔지니어 |
| 데이터 소스 | Tdoc 메타데이터 (Excel) |

### 1.2 Scope

| 포함 | 제외 |
| --- | --- |
| Tdoc 메타데이터 | TS/TR 본문 |
| Tdoc 간 관계 (revision, LS) | Final Minutes 본문 (2차에서) |
| 회의 정보 | RAN4/5 데이터 |
| 회사 정보 |  |
| Work Item / Agenda Item |  |
| Release 정보 |  |

### 1.3 1차 Competency Questions (25개) - 확정

**Tdoc 기본 검색 (9개)**

| # | 질문 |
| --- | --- |
| 1 | 특정 회의에서 특정 Work Item 관련 Tdoc 목록은? |
| 2 | 특정 회의에서 특정 Agenda Item 관련 Tdoc 목록은? |
| 3 | 특정 회의에서 특정 회사가 제출한 Tdoc 목록은? |
| 4 | 특정 Release에서 논의된 Tdoc 목록은? |
| 5 | 특정 회의에서 승인/합의된 Tdoc 목록은? |
| 6 | 특정 Tdoc의 결정 결과(Status)는? |
| 7 | 특정 Tdoc의 목적(For)은? |
| 8 | 특정 Tdoc의 담당자(Contact)는? |
| 9 | 이번 회의 전체 Agenda 목록과 설명은? |

**Tdoc 관계 추적 (7개)**

| # | 질문 |
| --- | --- |
| 10 | 특정 Tdoc의 이전/이후 revision은? |
| 11 | 특정 LS가 어디서 왔고 어디로 갔나? |
| 12 | 특정 Tdoc이 어떤 LS의 답변(Reply)인가? |
| 13 | 특정 Tdoc이 어떤 TS/Spec을 변경하나? |
| 14 | 특정 CR의 카테고리와 영향 범위는? |
| 15 | 이번 회의에서 다음 회의로 연기된 Tdoc은? |
| 16 | 이번 회의에 들어온 LS 목록과 관련 Agenda Item은? |

**회사/경쟁사 분석 (6개)**

| # | 질문 |
| --- | --- |
| 17 | 특정 회사가 특정 Work Item에서 낸 기고 목록은? |
| 18 | 특정 Agenda Item 관련 다른 회사 기고 목록은? |
| 19 | 특정 Work Item에서 회사별 기고 수는? |
| 20 | 특정 회사의 Tdoc 중 채택된 비율은? |
| 21 | 특정 Tdoc과 같은 Agenda Item에서 다른 회사가 낸 Tdoc 목록은? |
| 22 | 특정 회사의 주력 기술 영역(Work Item별 기고 분포)은? |

**히스토리/요약 (3개)**

| # | 질문 |
| --- | --- |
| 23 | 특정 기술에서 우리 회사가 이전 회의들에서 낸 기고 목록은? |
| 24 | 이번 회의에서 우리 회사 기고 결과 요약은? |
| 25 | 특정 Agenda Item에서 아직 미결(not treated)인 Tdoc은? |

---

### CQ 결과 규칙

### 정렬 기준 (Default Sort Order)

| CQ 그룹 | Primary Sort | Secondary Sort | 구현 속성 |
| --- | --- | --- | --- |
| Tdoc 기본 검색 (#1-9) | Meeting 번호 DESC | Agenda 번호 ASC, TDoc 번호 ASC | `meetingNumberInt DESC` |
| Tdoc 관계 추적 (#10-16) | TDoc 번호 ASC | - | `tdocNumber ASC` |
| 회사/경쟁사 분석 (#17-22) | Count DESC (많은 순) | Company 이름 ASC | `count DESC` |
| 히스토리/요약 (#23-25) | Meeting 번호 DESC | TDoc 번호 ASC | `meetingNumberInt DESC` |

*참고: "Meeting 번호 DESC"는 `meetingNumberInt` 속성으로 정렬해야 숫자 기반 정렬이 보장됨 (문자열 정렬 시 #99 > #122 문제 발생)*

### 결과 개수 (Default Limit)

| CQ 유형 | 기본값 | 적용 CQ |
| --- | --- | --- |
| 목록 조회 | 10 | #1-5, #9-12, #15-18, #21, #23, #25 |
| 단일 조회 | 1 | #6-8, #13-14 |
| 집계/순위 | 10 | #19-20, #22, #24 |

*참고: Limit은 쿼리 시 파라미터로 조정 가능*

## Competency Questions vs Tdoc 메타데이터 검증

## 검증 결과

| # | 질문 | 필요한 데이터 | 컬럼 존재 | 답변 가능 |
| --- | --- | --- | --- | --- |
| **Tdoc 기본 검색** |  |  |  |  |
| 1 | 특정 회의에서 특정 Work Item 관련 Tdoc 목록은? | Meeting, Related WIs | ⚠️ Meeting 컬럼 없음 | △ |
| 2 | 특정 회의에서 특정 Agenda Item 관련 Tdoc 목록은? | Meeting, Agenda item | ⚠️ Meeting 컬럼 없음 | △ |
| 3 | 특정 회의에서 특정 회사가 제출한 Tdoc 목록은? | Meeting, Source | ⚠️ Meeting 컬럼 없음 | △ |
| 4 | 특정 Release에서 논의된 Tdoc 목록은? | Release | ✅ | ✅ |
| 5 | 특정 회의에서 승인/합의된 Tdoc 목록은? | Meeting, TDoc Status | ⚠️ Meeting 컬럼 없음 | △ |
| 6 | 특정 Tdoc의 결정 결과(Status)는? | TDoc Status | ✅ | ✅ |
| 7 | 특정 Tdoc의 목적(For)은? | For | ✅ | ✅ |
| 8 | 특정 Tdoc의 담당자(Contact)는? | Contact | ✅ | ✅ |
| 9 | 이번 회의 전체 Agenda 목록과 설명은? | Agenda item, description | ✅ | ✅ |
| **Tdoc 관계 추적** |  |  |  |  |
| 10 | 특정 Tdoc의 이전/이후 revision은? | Is revision of, Revised to | ✅ | ✅ |
| 11 | 특정 LS가 어디서 왔고 어디로 갔나? | Original LS, To, Cc | ✅ | ✅ |
| 12 | 특정 Tdoc이 어떤 LS의 답변(Reply)인가? | Reply to, Reply in | ✅ | ✅ |
| 13 | 특정 Tdoc이 어떤 TS/Spec을 변경하나? | Spec | ✅ | ✅ |
| 14 | 특정 CR의 카테고리와 영향 범위는? | CR category, Clauses Affected | ✅ | ✅ |
| 15 | 이번 회의에서 다음 회의로 연기된 Tdoc은? | TDoc Status (postponed) | ✅ | ✅ |
| 16 | 이번 회의에 들어온 LS 목록과 관련 Agenda Item은? | Type (LS in), Agenda item | ✅ | ✅ |
| **회사/경쟁사 분석** |  |  |  |  |
| 17 | 특정 회사가 특정 Work Item에서 낸 기고 목록은? | Source, Related WIs | ✅ | ✅ |
| 18 | 특정 Agenda Item 관련 다른 회사 기고 목록은? | Agenda item, Source | ✅ | ✅ |
| 19 | 특정 Work Item에서 회사별 기고 수는? | Related WIs, Source | ✅ | ✅ |
| 20 | 특정 회사의 Tdoc 중 채택된 비율은? | Source, TDoc Status | ✅ | ✅ |
| 21 | 특정 Tdoc과 같은 Agenda Item에서 다른 회사가 낸 Tdoc 목록은? | Agenda item, Source | ✅ | ✅ |
| 22 | 특정 회사의 주력 기술 영역(Work Item별 기고 분포)은? | Source, Related WIs | ✅ | ✅ |
| **히스토리/요약** |  |  |  |  |
| 23 | 특정 기술에서 우리 회사가 이전 회의들에서 낸 기고 목록은? | 여러 회의 데이터 | ❌ 현재 1개 회의만 | ❌ |
| 24 | 이번 회의에서 우리 회사 기고 결과 요약은? | Source, TDoc Status | ✅ | ✅ |
| 25 | 특정 Agenda Item에서 아직 미결(not treated)인 Tdoc은? | Agenda item, TDoc Status | ✅ | ✅ |

---

## 발견된 문제

| 문제 | 해당 질문 | 해결 방법 |
| --- | --- | --- |
| **Meeting 컬럼 없음** | #1, #2, #3, #5 | TDoc 번호에서 추출 가능 (R1-25xxxxx → 2025년, 회의번호는 파일명에서) |
| **여러 회의 데이터 필요** | #23 | 현재 1개 회의만 보유 → 향후 데이터 추가 시 가능 |

---

## 결론

| 구분 | 개수 |
| --- | --- |
| ✅ 바로 답변 가능 | 20개 |
| △ Meeting 정보 추가 필요 | 4개 (#1, #2, #3, #5) |
| ❌ 데이터 부족 | 1개 (#23) |

---

## 제안

| 제안 | 설명 |
| --- | --- |
| **Meeting 클래스 추가** | 파일명/TDoc 번호에서 회의 정보 추출하여 Ontology에 포함 |
| **#23 유지** | 향후 여러 회의 데이터 추가 시 사용 가능하도록 구조만 준비 |

## Step 2: 기존 Ontology 재사용 검토

### 2.1 검토 결과

| 검토 대상 | 결과 |
| --- | --- |
| 3GPP Tdoc 전용 Ontology | ❌ 없음 |
| 통신 표준 문서 Ontology | ❌ 없음 |

**→ 3GPP 특화 Ontology는 직접 설계해야 함**

---

### 2.2 재사용 가능한 기존 Ontology

| Ontology | 정의 | 우리 용도 |
| --- | --- | --- |
| **Dublin Core (DC)** | 문서 메타데이터 표준 (제목, 작성자, 날짜 등 15개 요소) | Tdoc 기본 속성 |
| **FOAF** | 사람/조직 표현 표준 | Company, Contact |
| **SKOS** | 계층적 분류 체계 표현 표준 (상위-하위 관계) | Agenda Item 계층 (참고) |

---

### 2.3 재사용 매핑

| 우리 개념 | 기존 Ontology | 매핑 |
| --- | --- | --- |
| Tdoc 제목 | Dublin Core | dc:title |
| Tdoc 번호 | Dublin Core | dc:identifier |
| Tdoc 유형 | Dublin Core | dc:type |
| Tdoc 날짜 | Dublin Core | dc:date |
| Company | FOAF | foaf:Organization |
| Contact | FOAF | foaf:Person |
| Agenda 계층 | SKOS | skos:broader, skos:narrower (참고) |

---

### 2.4 직접 정의해야 할 것 (3GPP 특화)

| 개념 | 데이터 소스 (Tdoc_list 컬럼) |
| --- | --- |
| Tdoc | TDoc, Title, Abstract |
| Meeting | 파일명/TDoc 번호에서 추출 |
| Work Item | Related WIs |
| Agenda Item | Agenda item, Agenda item description |
| Release | Release |
| Spec (TS/TR) | Spec, Version |
| Company | Source |
| Contact | Contact, Contact ID |
| LS 관계 | Reply to, To, Cc, Original LS, Reply in |
| Revision 관계 | Is revision of, Revised to |
| CR 관련 | CR, CR category, Clauses Affected |
| TDoc Status | TDoc Status |
| For (목적) | For |
| Type | Type |

---

### 2.5 결론

| 구분 | 내용 |
| --- | --- |
| **재사용** | Dublin Core, FOAF, SKOS 개념 참조 |
| **신규 정의** | 3GPP 특화 클래스 및 관계 |
| **데이터 소스** | 모두 Tdoc_list 메타데이터로 커버 가능 ✅ |

## Step 3: 중요 용어 나열

### 3.1 목적

> 도메인에서 나오는 명사, 동사를 전부 나열하되, Tdoc_list로 채울 수 있는지 검증
> 

**데이터 소스**: TDoc_List_Meeting_RAN1_120_final_.xlsx (RAN1#120 회의)

---

### 3.2 클래스 후보 (11개)

| 용어 | 데이터 소스 | 채울 수 있나? | 비고 (RAN1#120 기준) |
| --- | --- | --- | --- |
| Tdoc | TDoc 컬럼 | ✅ | 상위 클래스, 1,674건 |
| CR | Type 컬럼 (CR, draftCR) | ✅ | Tdoc 하위 클래스 |
| LS | Type 컬럼 (LS in, LS out) | ✅ | Tdoc 하위 클래스 |
| Meeting | 파일명에서 추출 | ✅ | RAN1#120 |
| Company | Source 컬럼 | ✅ | 166개 (파싱/정규화 필요) |
| Contact | Contact 컬럼 | ✅ | 209명 |
| WorkItem | Related WIs 컬럼 | ✅ | 67개 (파싱 필요) |
| AgendaItem | Agenda item 컬럼 | ✅ | 64개 |
| Release | Release 컬럼 | ✅ | 5개 (Rel-15~19) |
| Spec | Spec 컬럼 | ✅ | 7개 |
| WorkingGroup | To, Cc에서 추출 | ✅ | 10개 (파싱 필요) |

---

### 3.3 Object Property 후보 (14개)

| 용어 | 데이터 소스 | 설명 | 채울 수 있나? | 비고 (RAN1#120 기준) |
| --- | --- | --- | --- | --- |
| submittedBy | Source | Tdoc → Company | ✅ |  |
| hasContact | Contact | Tdoc → Contact | ✅ |  |
| relatedTo | Related WIs | Tdoc → Work Item (다대다) | ✅ |  |
| belongsTo | Agenda item | Tdoc → Agenda Item | ✅ |  |
| targetRelease | Release | Tdoc → Release | ✅ |  |
| modifies | Spec | Tdoc → Spec | ✅ | 84건 |
| presentedAt | 파일명 | Tdoc → Meeting | ✅ |  |
| isRevisionOf | Is revision of | Tdoc → Tdoc | ✅ | 74건 |
| revisedTo | Revised to | Tdoc → Tdoc | ✅ | 77건 |
| replyTo | Reply to | Tdoc → Tdoc | ✅ | 89건 |
| originalLS | Original LS | Tdoc → Tdoc | ✅ | 32건 |
| replyIn | Reply in | Tdoc → Tdoc | ✅ | 13건 |
| sentTo | To | Tdoc → Working Group (다대다) | ✅ | 137건 |
| ccTo | Cc | Tdoc → Working Group (다대다) | ✅ | 54건 |

---

### 3.4 Data Property 후보 (20개)

| 용어 | 데이터 소스 | 대상 클래스 | 채울 수 있나? | 비고 (RAN1#120 기준) |
| --- | --- | --- | --- | --- |
| tdocNumber | TDoc | Tdoc | ✅ | 1,674건 |
| title | Title | Tdoc | ✅ | 1,674건 |
| abstract | Abstract | Tdoc | ✅ | 46건 |
| type | Type | Tdoc | ✅ | 1,674건 |
| status | TDoc Status | Tdoc | ✅ | 1,674건 |
| for | For | Tdoc | ✅ | 1,537건 |
| reservationDate | Reservation date | Tdoc | ✅ | 1,674건 |
| uploadedDate | Uploaded | Tdoc | ✅ | 1,658건 |
| secretaryRemarks | Secretary Remarks | Tdoc | ✅ | 43건 |
| contactId | Contact ID | Contact | ✅ | 1,674건 |
| agendaDescription | Agenda item description | Agenda Item | ✅ | 64개 |
| specVersion | Version | Spec 관계 | ✅ | 80건 |
| crNumber | CR | Tdoc | ✅ | 19건 |
| crCategory | CR category | Tdoc | ✅ | 65건 |
| clausesAffected | Clauses Affected | Tdoc | ✅ | 12건 |
| tsgCRPack | TSG CR Pack | Tdoc | ✅ | 19건 |
| affectsUICC | UICC | Tdoc | ✅ | 12건 |
| affectsME | ME | Tdoc | ✅ | 12건 |
| affectsRAN | RAN | Tdoc | ✅ | 12건 |
| affectsCN | CN | Tdoc | ✅ | 12건 |

---

### 3.5 제외 (3개)

| 컬럼 | 제외 이유 |
| --- | --- |
| Agenda item sort order | 정렬용, Ontology 불필요 |
| TDoc sort order within agenda item | 정렬용, Ontology 불필요 |
| CR revision | 데이터 없음 (0건) |

---

### 3.6 용어 목록 요약

| 구분 | 개수 |
| --- | --- |
| 클래스 후보 | 11개 |
| Object Property 후보 | 14개 |
| Data Property 후보 | 20개 |
| **총계** | **45개** |

---

### 3.7 파싱 필요 사항

| 컬럼 | 이유 | 예시 |
| --- | --- | --- |
| Source | 복합 값 | "RAN1 Chair, ETSI MCC" → 2개 Company |
| Related WIs | 복합 값 | "NR_MIMO_Ph5-Core, NR_duplex" → 2개 Work Item |
| To | 복합 값 | "RAN1, RAN4" → 2개 Working Group |
| Cc | 복합 값 | "RAN, RAN1, SA2" → 3개 Working Group |

## Step 4: 클래스와 계층 구조 정의

### 4.1 목적

> Step 3에서 나열한 용어 중 클래스를 확정하고, **계층 구조(is-a 관계)**를 정의
> 

**데이터 소스**: TDoc_List_Meeting_RAN1_120_final_.xlsx (RAN1#120 회의)

---

### 4.2 클래스 확정 (11개)

| 클래스 | 설명 | 채울 수 있나? | 비고 (RAN1#120 기준) |
| --- | --- | --- | --- |
| Tdoc | 3GPP 회의 문서 | ✅ | 1,457건 |
| CR | Change Request (Tdoc 하위) | ✅ | 80건 (CR 19 + draftCR 61) |
| LS | Liaison Statement (Tdoc 하위) | ✅ | 137건 (out 105 + in 32) |
| Meeting | 3GPP 회의 | ✅ | 파일명에서 추출 |
| Company | 기고 회사/조직 | ✅ | 212개 (파싱 필요) |
| Contact | 담당자 | ✅ | 1,674건 |
| WorkItem | 작업 항목 | ✅ | 67개 (파싱 필요) |
| AgendaItem | 회의 안건 | ✅ | 64개 |
| Release | 3GPP 릴리즈 | ✅ | 5개 (Rel-15~19) |
| Spec | 기술 규격 (TS/TR) | ✅ | 84건 |
| WorkingGroup | 3GPP 작업 그룹 | ✅ | To, Cc에서 추출 |

---

### 4.3 클래스 계층 구조

```
Tdoc
├── CR
└── LS

Meeting
Company
Contact
WorkItem
AgendaItem
Release
Spec
WorkingGroup

```

---

### 4.4 하위 클래스 판단 근거

| 클래스 | 근거 |
| --- | --- |
| CR | 고유 속성 8개 (crNumber, crCategory 등) + 고유 관계 (modifies→Spec) |
| LS | 도메인 특성 (WG 간 공식 소통), 고유 관계 (sentTo, ccTo→WorkingGroup) |

---

### 4.5 Type별 클래스 매핑

| Type | 클래스 | 구분 속성 |
| --- | --- | --- |
| CR | CR | - |
| draftCR | CR | crNumber가 null |
| pCR | CR | crNumber가 null (draftCR과 동일 처리) |
| LS out | LS | direction = 'out' |
| LS in | LS | direction = 'in' |
| discussion | Tdoc | type = 'discussion' |
| other | Tdoc | type = 'other' |
| report | Tdoc | type = 'report' |
| agenda | Tdoc | type = 'agenda' |
| Work Plan | Tdoc | type = 'Work Plan' |
| draft TR | Tdoc | type = 'draft TR' |
| draft TS | Tdoc | type = 'draft TS' |
| response | Tdoc | type = 'response' |
| WID new | Tdoc | type = 'WID new' |
| SID new | Tdoc | type = 'SID new' |
| WI summary | Tdoc | type = 'WI summary' |

---

### 4.6 하위 클래스 상세

### CR (Change Request)

| 항목 | 내용 |
| --- | --- |
| 상속 | Tdoc의 모든 속성/관계 |
| 고유 Data Property | crNumber, crCategory, clausesAffected, tsgCRPack, affectsUICC, affectsME, affectsRAN, affectsCN |
| 고유 Object Property | modifies → Spec |
| 해당 Type | 'CR', 'draftCR', 'pCR’ |
| draftCR 구분 | crNumber가 null |

### LS (Liaison Statement)

| 항목 | 내용 |
| --- | --- |
| 상속 | Tdoc의 모든 속성/관계 |
| 고유 Data Property | direction ('in' / 'out') |
| 고유 Object Property | sentTo → WorkingGroup, ccTo → WorkingGroup, originalLS → Tdoc (direction='in'일 때만) |
| 해당 Type | 'LS out', 'LS in' |
| 방향 구분 | direction 속성 |

---

### 4.7 클래스별 인스턴스 수 (RAN1#120 기준)

| 클래스 | 건수 | 비율 |
| --- | --- | --- |
| Tdoc (직접) | 1,457건 | 87.0% |
| CR | 80건 | 4.8% |
| LS | 137건 | 8.2% |
| **총계** | **1,674건** | **100%** |

---

### 4.8 검증 결과

| 검증 항목 | 결과 |
| --- | --- |
| 모든 Tdoc 분류됨 | ✅ 1,674건 = 1,674건 |
| CR 고유 속성 확인 | ✅ crNumber, Spec 등 |
| LS direction 구분 | ✅ out 105건, in 32건 |
| LS originalLS (in 전용) | ✅ out 0건, in 32건 |

## Step 5: 속성(Slot) 정의

### 5.1 목적

> 각 클래스의 **Object Property (관계)**와 **Data Property (속성)**를 정의하고, 각 속성의 의미와 용도를 명확히 기술
> 

**데이터 소스**: TDoc_List_Meeting_RAN1_120_final_.xlsx (RAN1#120 회의)

---

### 5.2 속성 요약

| 구분 | 개수 |
| --- | --- |
| Object Property | 14개 |
| Data Property | 30개 |
| **총계** | **44개** |

---

### 5.3 Tdoc 클래스 속성

### Object Property (10개)

| 속성명 | Range | 데이터 소스 | 설명 |
| --- | --- | --- | --- |
| submittedBy | Company | Source | Tdoc을 제출한 회사/조직. 복수 회사가 공동 제출 가능 |
| hasContact | Contact | Contact | Tdoc의 담당자 (연락 가능한 사람) |
| relatedTo | WorkItem | Related WIs | Tdoc이 관련된 Work Item. 하나의 Tdoc이 여러 WI에 관련될 수 있음 |
| belongsTo | AgendaItem | Agenda item | Tdoc이 논의되는 Agenda Item |
| targetRelease | Release | Release | Tdoc이 대상으로 하는 3GPP Release 버전 |
| presentedAt | Meeting | 파일명 | Tdoc이 발표/논의된 3GPP 회의 |
| isRevisionOf | Tdoc | Is revision of | 이 Tdoc이 수정한 이전 버전 Tdoc (예: R1-2500138은 R1-2500001의 revision) |
| revisedTo | Tdoc | Revised to | 이 Tdoc을 수정한 이후 버전 Tdoc (isRevisionOf의 역관계) |
| replyTo | Tdoc | Reply to | 이 Tdoc이 답변하는 대상 Tdoc (주로 LS에 대한 답변) |
| replyIn | Tdoc | Reply in | 이 Tdoc에 대한 답변 Tdoc (replyTo의 역관계) |

### Data Property (9개)

| 속성명 | Type | 데이터 소스 | 설명 |
| --- | --- | --- | --- |
| tdocNumber | String | TDoc | Tdoc의 고유 식별자 (예: R1-2500001). 형식: R1-YYNNNNN |
| title | String | Title | Tdoc의 제목. 문서 내용을 요약하는 짧은 설명 |
| abstract | String | Abstract | Tdoc의 요약. 문서 내용의 상세 설명 (대부분 비어있음) |
| type | String (Enum) | Type | Tdoc의 유형. 허용값: discussion, CR, draftCR, pCR, LS out, LS in, other, report, agenda, Work Plan, draft TR, draft TS, response, WID new, SID new, WI summary |
| status | String (Enum) | TDoc Status | 회의에서의 결정 결과. 허용값: approved, agreed, noted, revised, postponed, withdrawn, not treated 등 |
| for | String (Enum) | For | Tdoc의 목적/용도. 허용값: Decision, Discussion, Approval, Agreement, Endorsement, Information |
| reservationDate | DateTime | Reservation date | Tdoc 번호 예약 일시 |
| uploadedDate | DateTime | Uploaded | Tdoc 파일 업로드 일시 |
| secretaryRemarks | String | Secretary Remarks | 회의 비서의 메모 (예: "Late contribution", "Revised in session") |

---

### 5.4 CR 클래스 속성 (Tdoc 상속 + 추가)

> CR (Change Request)은 3GPP 기술 규격(TS/TR)의 변경을 요청하는 공식 문서
> 

### 추가 Object Property (1개)

| 속성명 | Range | 데이터 소스 | 설명 |
| --- | --- | --- | --- |
| modifies | Spec | Spec | CR이 변경을 요청하는 대상 기술 규격 (예: 38.212) |

### 추가 Data Property (8개)

| 속성명 | Type | 데이터 소스 | 설명 |
| --- | --- | --- | --- |
| crNumber | String | CR | CR의 공식 번호 (예: 0693). draftCR은 이 값이 없음 |
| crCategory | String (Enum) | CR category | CR의 카테고리. F(Fix), A(Addition), B(Backward compatible), D(Deletion) |
| clausesAffected | String | Clauses Affected | CR로 인해 영향받는 규격의 조항 번호 (예: "5.3.1, 5.3.2") |
| tsgCRPack | String | TSG CR Pack | TSG에 제출되는 CR Pack 번호 (예: RP-250233) |
| affectsUICC | Boolean | UICC | CR이 UICC(Universal Integrated Circuit Card)에 영향을 미치는지 여부 |
| affectsME | Boolean | ME | CR이 ME(Mobile Equipment)에 영향을 미치는지 여부 |
| affectsRAN | Boolean | RAN | CR이 RAN(Radio Access Network)에 영향을 미치는지 여부 |
| affectsCN | Boolean | CN | CR이 CN(Core Network)에 영향을 미치는지 여부 |

---

### 5.5 LS 클래스 속성 (Tdoc 상속 + 추가)

> LS (Liaison Statement)는 3GPP Working Group 간 또는 외부 조직과의 공식 소통 문서
> 

### 추가 Object Property (3개)

| 속성명 | Range | 데이터 소스 | 설명 |
| --- | --- | --- | --- |
| sentTo | WorkingGroup | To | LS의 수신 대상 Working Group (예: RAN1, RAN4). 복수 가능 |
| ccTo | WorkingGroup | Cc | LS의 참조 대상 Working Group. 복수 가능 |
| originalLS | Tdoc | Original LS | LS in의 경우, 다른 WG에서 보낸 원본 LS 문서 번호 (예: R2-2410957) |

### 추가 Data Property (1개)

| 속성명 | Type | 데이터 소스 | 설명 |
| --- | --- | --- | --- |
| direction | String (Enum) | Type에서 추출 | LS의 방향. in(수신), out(발신) |

---

### 5.6 기타 클래스 속성

### Meeting (4개)

| 속성명 | Type | 데이터 소스 | 설명 |
| --- | --- | --- | --- |
| meetingNumber | String | 파일명 | 회의 번호 원본 (예: RAN1#120, RAN1#101-e). 형식: {WG}#{회차}[-e] |
| canonicalMeetingNumber | String | meetingNumber에서 정규화 | 정규화된 회의 번호. `-e` suffix 제거 |
| meetingNumberInt | Integer | canonicalMeetingNumber에서 추출 | 정렬용 숫자값. CQ 결과의 "Meeting 번호 DESC" 정렬에 사용 |
| workingGroup | String | 파일명 | 회의를 주관하는 Working Group (예: RAN1) |

**Meeting ID 정규화 규칙:**

| 원본 | 정규화 | 설명 |
| --- | --- | --- |
| RAN1#101-e | RAN1#101 | e-meeting suffix 제거 |
| RAN1#112bis-e | RAN1#112bis | e-meeting suffix만 제거, bis 유지 |
| RAN1#120 | RAN1#120 | 변경 없음 |
- `e` suffix: e-meeting 표시로, 정규화 시 제거
- `bis`, `ter`, `b` suffix: 회차 구분이므로 유지

### meetingNumberInt 추출 규칙

| canonicalMeetingNumber | meetingNumberInt | 설명 |
| --- | --- | --- |
| RAN1#122 | 122 | 숫자만 추출 |
| RAN1#99 | 99 | 숫자만 추출 |
| RAN1#112bis | 112 | suffix(bis, ter, b) 제외, 숫자만 |
| RAN1#100 | 100 | 숫자만 추출 |

**추출 로직**: `canonicalMeetingNumber`에서 `#` 뒤의 숫자만 추출 (정규식: `#(\\d+)`)

### COVID-era e-meeting 특이사항

COVID-19로 인해 RAN1#100 대면 회의가 중단되고, RAN1#100-e로 e-meeting 재개되어 완료된 사례가 있습니다.

| 대면 회의 | e-meeting | 상태 |
| --- | --- | --- |
| RAN1#100 | RAN1#100-e | 대면 회의 중단 → e-meeting으로 완료 |

**데이터 특성:**

- **Final Report**: RAN1#100-e에만 존재 (RAN1#100 + RAN1#100-e 내용 모두 포함)
- **Tdoc**: 두 Meeting 모두에 존재 가능

**처리 원칙:**

1. 두 Meeting 노드 모두 유지 (별도 노드)
2. canonicalMeetingNumber 동일 (`"RAN1#100"`)
3. 2단계 Resolution은 canonicalMeetingNumber로 매칭되어 **두 Meeting 모두에 연결됨**

### Company (1개)

| 속성명 | Type | 데이터 소스 | 설명 |
| --- | --- | --- | --- |
| companyName | String | Source 파싱 | 회사/조직의 이름 (예: Samsung, Huawei, Ericsson, ETSI MCC) |

### Contact (2개)

| 속성명 | Type | 데이터 소스 | 설명 |
| --- | --- | --- | --- |
| contactName | String | Contact | 담당자의 이름 (예: Patrick Merias) |
| contactId | String | Contact ID | 3GPP 시스템에서의 담당자 고유 ID (예: 52292) |

### WorkItem (1개)

| 속성명 | Type | 데이터 소스 | 설명 |
| --- | --- | --- | --- |
| workItemCode | String | Related WIs 파싱 | Work Item의 코드명 (예: NR_MIMO_Ph5-Core, NR_AIML_air-Core) |

### AgendaItem (2개)

| 속성명 | Type | 데이터 소스 | 설명 |
| --- | --- | --- | --- |
| agendaNumber | String | Agenda item | Agenda Item의 번호 (예: 9.1, 9.1.1). 계층 구조를 가짐 |
| agendaDescription | String | Agenda item description | Agenda Item의 설명 (예: "AI/ML for NR Air Interface") |

### Release (1개)

| 속성명 | Type | 데이터 소스 | 설명 |
| --- | --- | --- | --- |
| releaseName | String | Release | 3GPP Release 버전명 (예: Rel-18, Rel-19) |

### Spec (2개)

| 속성명 | Type | 데이터 소스 | 설명 |
| --- | --- | --- | --- |
| specNumber | String | Spec | 기술 규격 번호 (예: 38.212, 38.214). TS/TR 시리즈 |
| specVersion | String | Version | 규격의 버전 (예: 18.5.0) |

### WorkingGroup (1개)

| 속성명 | Type | 데이터 소스 | 설명 |
| --- | --- | --- | --- |
| wgName | String | To, Cc 파싱 | Working Group 이름 (예: RAN1, RAN2, SA2) |

---

### 5.7 컬럼 매핑 요약

| 구분 | 개수 |
| --- | --- |
| 사용 컬럼 | 33개 |
| 제외 컬럼 | 3개 (정렬용 2개, 데이터 없음 1개) |
| **총 컬럼** | **36개** |

---

### 5.8 컬럼 구조 참고

| 미팅 범위 | 컬럼 수 | 비고 |
| --- | --- | --- |
| RAN1#84 ~ #107-e | 31개 | CR 영향 컬럼 5개 없음 (CN, ME, RAN, UICC, Clauses Affected) |
| RAN1#107b-e ~ #122b | 36개 | 전체 컬럼 |

---

### 5.9 파싱 필요 항목

| 항목 | 원본 예시 | 파싱 결과 | 설명 |
| --- | --- | --- | --- |
| Source | "Samsung, Huawei" | Company 2개 | 쉼표로 분리하여 복수 Company 생성 |
| Related WIs | "NR_MIMO_Ph5-Core, NR_duplex" | WorkItem 2개 | 쉼표로 분리하여 복수 WorkItem 생성 |
| To, Cc | "RAN1, RAN4" | WorkingGroup 2개 | 쉼표로 분리하여 복수 WorkingGroup 생성 |
| 파일명 | "TDoc_List_Meeting_RAN1_120..." | Meeting: RAN1#120 | 정규식으로 WG명과 회차 추출 |
| Type | "LS in" / "LS out" | direction: "in" / "out" | Type 값에서 방향만 추출 |

---

### 5.10 검증 결과

| 항목 | 결과 |
| --- | --- |
| 모든 컬럼 매핑 | ✅ |
| CQ 답변 가능 | ✅ 24/25개 |
| Tdoc_list만으로 구축 | ✅ |

## CQ23

> "특정 기술에서 우리 회사가 이전 회의들에서 낸 기고 목록은?"
> 

---

## 이유

| 항목 | 내용 |
| --- | --- |
| 현재 데이터 | RAN1#120 회의 1개만 |
| CQ23 요구 | **여러 회의** 데이터 필요 |
| 결론 | 1차 Ontology로는 부분 답변만 가능 |

---

## 해결 방법

| 시점 | 방법 |
| --- | --- |
| 현재 (1차) | RAN1#120 내에서만 답변 가능 (△) |
| 향후 | 여러 회의의 Tdoc_list를 추가하면 완전 답변 가능 (✅) |

## Step 6: 속성의 제약조건 (Facets) 정의

### 6.1 목적

> 각 속성의 Cardinality (개수), Domain/Range, 필수 여부, Enumeration (열거형) 등 제약조건을 정의하고, 각 제약조건의 근거와 의미를 명확히 기술
> 

**데이터 소스**: TDoc_List_Meeting_RAN1_120_final_.xlsx (RAN1#120 회의)

---

### 6.2 Cardinality 표기법

| 표기 | 의미 | 설명 |
| --- | --- | --- |
| 1 | 정확히 1개 | 필수, 단일 값 |
| 0..1 | 0개 또는 1개 | 선택, 단일 값 |
| 1..* | 1개 이상 | 필수, 복수 값 가능 |
| 0..* | 0개 이상 | 선택, 복수 값 가능 |

---

### 6.3 Tdoc 클래스 속성 제약조건

### Object Property

| 속성명 | Domain | Range | Cardinality | 필수 | 근거 (RAN1#120) |
| --- | --- | --- | --- | --- | --- |
| submittedBy | Tdoc | Company | 1..* | ✅ | 모든 Tdoc에 Source 존재 (1,674건). 복수 회사 공동 제출 가능 (402건이 쉼표 포함) |
| hasContact | Tdoc | Contact | 1 | ✅ | 모든 Tdoc에 Contact 존재 (1,674건). 담당자는 1명 |
| relatedTo | Tdoc | WorkItem | 0..* | ❌ | 12건은 Related WIs 없음. 복수 WI 관련 가능 (43건이 쉼표 포함) |
| belongsTo | Tdoc | AgendaItem | 1 | ✅ | 모든 Tdoc에 Agenda item 존재 (1,674건) |
| targetRelease | Tdoc | Release | 0..1 | ❌ | 6건은 Release 없음. 하나의 Release만 대상 |
| presentedAt | Tdoc | Meeting | 1 | ✅ | 모든 Tdoc은 특정 회의에 속함 |
| isRevisionOf | Tdoc | Tdoc | 0..1 | ❌ | 74건만 이전 revision 존재. 최초 버전은 없음 |
| revisedTo | Tdoc | Tdoc | 0..1 | ❌ | 77건만 이후 revision 존재. 최종 버전은 없음 |
| replyTo | Tdoc | Tdoc | 0..1 | ❌ | 89건만 답변 대상 존재. 주로 LS에서 사용 |
| replyIn | Tdoc | Tdoc | 0..1 | ❌ | 13건만 답변 문서 존재 |

### Data Property

| 속성명 | Domain | Type | Cardinality | 필수 | 근거 (RAN1#120) |
| --- | --- | --- | --- | --- | --- |
| tdocNumber | Tdoc | String | 1 | ✅ | 모든 Tdoc의 고유 식별자 (1,674건) |
| title | Tdoc | String | 1 | ✅ | 모든 Tdoc에 제목 존재 (1,674건) |
| abstract | Tdoc | String | 0..1 | ❌ | 46건만 요약 존재. 대부분 비어있음 |
| type | Tdoc | String (Enum) | 1 | ✅ | 모든 Tdoc에 유형 존재 (1,674건) |
| status | Tdoc | String (Enum) | 1 | ✅ | 모든 Tdoc에 상태 존재 (1,674건) |
| for | Tdoc | String (Enum) | 0..1 | ❌ | 137건은 For 없음 (주로 LS) |
| reservationDate | Tdoc | DateTime | 1 | ✅ | 모든 Tdoc에 예약일 존재 (1,674건) |
| uploadedDate | Tdoc | DateTime | 0..1 | ❌ | 16건은 업로드일 없음 (미업로드 문서) |
| secretaryRemarks | Tdoc | String | 0..1 | ❌ | 43건만 비서 메모 존재 |

---

### 6.4 CR 클래스 추가 속성 제약조건

> CR/draftCR 총 80건 기준
> 

### Object Property

| 속성명 | Domain | Range | Cardinality | 필수 | 근거 (RAN1#120) |
| --- | --- | --- | --- | --- | --- |
| modifies | CR | Spec | 1 | ✅ | 모든 CR/draftCR에 Spec 존재 (80건). CR은 반드시 특정 규격을 변경 |

### Data Property

| 속성명 | Domain | Type | Cardinality | 필수 | 근거 (RAN1#120) |
| --- | --- | --- | --- | --- | --- |
| crNumber | CR | String | 0..1 | ❌ | CR만 19건 존재. draftCR 61건은 아직 CR 번호 미부여 |
| crCategory | CR | String (Enum) | 0..1 | ❌ | 65건만 카테고리 존재. 15건은 미지정 |
| clausesAffected | CR | String | 0..1 | ❌ | 12건만 영향 조항 명시 |
| tsgCRPack | CR | String | 0..1 | ❌ | 19건만 TSG CR Pack 존재 (승인된 CR만) |
| affectsUICC | CR | Boolean | 0..1 | ❌ | 12건만 UICC 영향 여부 명시 |
| affectsME | CR | Boolean | 0..1 | ❌ | 12건만 ME 영향 여부 명시 |
| affectsRAN | CR | Boolean | 0..1 | ❌ | 12건만 RAN 영향 여부 명시 |
| affectsCN | CR | Boolean | 0..1 | ❌ | 12건만 CN 영향 여부 명시 |

---

### 6.5 LS 클래스 추가 속성 제약조건

> LS out 105건, LS in 32건, 총 137건 기준
> 

### Object Property

| 속성명 | Domain | Range | Cardinality | 필수 | 근거 (RAN1#120) |
| --- | --- | --- | --- | --- | --- |
| sentTo | LS | WorkingGroup | 1..* | ✅ | 모든 LS에 To 존재 (137건). LS는 반드시 수신처 필요. 복수 가능 (16건이 쉼표 포함) |
| ccTo | LS | WorkingGroup | 0..* | ❌ | 54건만 Cc 존재. 참조는 선택사항 |
| originalLS | LS | Tdoc | 0..1 | ❌ | LS in 32건만 존재. LS out은 원본 LS 없음 |

### Data Property

| 속성명 | Domain | Type | Cardinality | 필수 | 근거 (RAN1#120) |
| --- | --- | --- | --- | --- | --- |
| direction | LS | String (Enum) | 1 | ✅ | 모든 LS는 방향 있음. Type에서 추출 (in 또는 out) |

---

### 6.6 기타 클래스 속성 제약조건

### Meeting

| 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
| --- | --- | --- | --- | --- | --- |
| meetingNumber | Meeting | String | 1 | ✅ | 회의 번호 원본. 형식: {WG}#{회차}[-e] (예: RAN1#120, RAN1#101-e) |
| canonicalMeetingNumber | Meeting | String | 1 | ✅ | 정규화된 회의 번호. `-e` suffix 제거 (예: RAN1#120, RAN1#101) |
| meetingNumberInt | Meeting | Integer | 1 | ✅ | 정렬용 숫자값. `canonicalMeetingNumber`에서 파생 |
| workingGroup | Meeting | String | 1 | ✅ | 회의를 주관하는 Working Group |

**제약조건:**

- `canonicalMeetingNumber`는 `meetingNumber`에서 파생 (자동 생성)
- `meetingNumberInt`는 `canonicalMeetingNumber`에서 파생 (자동 생성, 정규식: `#(\\d+)`)
- `canonicalMeetingNumber`는 2단계 Resolution 연결 시 매칭 키로 사용
- `meetingNumberInt`는 CQ 결과 정렬 시 사용 (`ORDER BY meetingNumberInt DESC`)

### Company

| 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
| --- | --- | --- | --- | --- | --- |
| companyName | Company | String | 1 | ✅ | 회사/조직의 고유 이름 |

### Contact

| 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
| --- | --- | --- | --- | --- | --- |
| contactName | Contact | String | 1 | ✅ | 담당자의 이름 |
| contactId | Contact | String | 1 | ✅ | 3GPP 시스템의 담당자 고유 ID |

### WorkItem

| 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
| --- | --- | --- | --- | --- | --- |
| workItemCode | WorkItem | String | 1 | ✅ | Work Item의 고유 코드명 |

### AgendaItem

| 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
| --- | --- | --- | --- | --- | --- |
| agendaNumber | AgendaItem | String | 1 | ✅ | Agenda의 번호 (계층 구조: 9 > 9.1 > 9.1.1) |
| agendaDescription | AgendaItem | String | 1 | ✅ | Agenda의 설명/제목 |

### Release

| 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
| --- | --- | --- | --- | --- | --- |
| releaseName | Release | String | 1 | ✅ | Release 버전명 (예: Rel-18, Rel-19) |

### Spec

| 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
| --- | --- | --- | --- | --- | --- |
| specNumber | Spec | String | 1 | ✅ | 기술 규격의 고유 번호 (예: 38.212) |
| specVersion | Spec | String | 0..1 | ❌ | 규격의 버전. 80건만 존재 (4건은 버전 없음) |

### WorkingGroup

| 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
| --- | --- | --- | --- | --- | --- |
| wgName | WorkingGroup | String | 1 | ✅ | Working Group의 고유 이름 (예: RAN1, SA2) |

---

### 6.7 Inverse Property (역관계)

> 두 속성이 서로 역관계일 때, 한쪽 값을 설정하면 다른 쪽도 자동으로 추론 가능
> 

| 속성 | 역속성 | 설명 | 검증 (RAN1#120) |
| --- | --- | --- | --- |
| isRevisionOf | revisedTo | A가 B의 revision이면, B는 A로 revised됨 | 74건 일치 확인 |
| replyTo | replyIn | A가 B에 대한 답변이면, B는 A에서 답변됨 | 관계 존재 확인 |

---

### 6.8 Enumeration (열거형)

> 속성이 가질 수 있는 값을 제한하여 데이터 일관성 보장
> 

### type (Tdoc 유형)

| 값 | 설명 | 건수 (RAN1#84~#122b, 59개 미팅) |
| --- | --- | --- |
| discussion | 일반 기술 제안/논의 문서 | 90,860 |
| other | 기타 문서 | 13,950 |
| draftCR | Change Request 초안 (CR 번호 미부여) | 6,244 |
| LS out | 발신 Liaison Statement | 4,457 |
| CR | 공식 Change Request | 4,239 |
| LS in | 수신 Liaison Statement | 1,844 |
| draft TR | Technical Report 초안 | 253 |
| report | 보고서 | 87 |
| agenda | 회의 안건표 | 81 |
| draft TS | Technical Specification 초안 | 80 |
| Work Plan | 작업 계획 | 78 |
| pCR | Proposed CR (CR 초안, CR 클래스에 포함) | 61 |
| response | 응답 문서 | 17 |
| WID new | 새 Work Item Description | 3 |
| SID new | 새 Study Item Description | 2 |
| WI summary | Work Item 요약 | 1 |

### status (결정 상태)

| 값 | 설명 | 건수 (RAN1#84~#122b, 59개 미팅) |
| --- | --- | --- |
| not treated | 회의에서 다루지 않음 (시간 부족 등) | 53,884 |
| available | 접수됨 (회의 전 상태) | 24,881 |
| noted | 참고로 접수됨 | 20,354 |
| revised | 수정되어 새 버전으로 대체됨 | 8,280 |
| agreed | 합의됨 | 3,931 |
| withdrawn | 제출자가 철회함 | 2,803 |
| not pursued | 더 이상 추진하지 않음 | 2,507 |
| endorsed | 지지/승인됨 | 2,450 |
| approved | 공식 승인됨 | 1,516 |
| treated | 처리됨 | 1,249 |
| postponed | 다음 회의로 연기됨 | 318 |
| reserved | 예약됨 (번호만 할당) | 49 |
| merged | 다른 문서와 병합됨 | 33 |
| not concluded | 결론 미도출 | 1 |
| conditionally agreed | 조건부 합의 | 1 |

### for (문서 목적)

| 값 | 설명 | 건수 (RAN1#84~#122b, 59개 미팅) |
| --- | --- | --- |
| Decision | 결정 요청 | 78,564 |
| Discussion | 논의 요청 | 12,781 |
| Agreement | 합의 요청 | 3,405 |
| Approval | 승인 요청 | 1,970 |
| Endorsement | 지지 요청 | 1,139 |
| Information | 정보 공유 | 1,022 |
| Presentation | 발표용 | 2 |
| Action | 조치 요청 | 2 |

### direction (LS 방향)

| 값 | 설명 | 건수 (RAN1#84~#122b, 59개 미팅) |
| --- | --- | --- |
| out | 이 WG에서 다른 WG로 발신 | 4,457 |
| in | 다른 WG에서 이 WG로 수신 | 1,844 |

### crCategory (CR 카테고리)

| 값 | 설명 | 건수 (RAN1#84~#122b, 59개 미팅) |
| --- | --- | --- |
| F | Correction (오류 수정) | 7,546 |
| B | Addition of feature (기능 추가, 하위 호환) | 961 |
| A | Mirror CR (다른 Release에 동일 적용) | 797 |
| D | Editorial change (편집상 변경) | 80 |
| C | Functional modification of feature (기능 수정) | 11 |
| E | Early implementation (조기 구현) | 1 |

### Release 값

| 값 | 건수 (RAN1#84~#122b, 59개 미팅) |
| --- | --- |
| Rel-17 | 21,388 |
| Rel-18 | 19,728 |
| Rel-19 | 13,477 |
| Rel-16 | 13,124 |
| Rel-15 | 8,805 |
| Rel-14 | 3,283 |
| Rel-13 | 1,482 |
| Rel-20 | 1,240 |
| Rel-12 | 85 |
| Rel-9 | 6 |
| Rel-11 | 5 |
| Rel-10 | 2 |
| Rel-8 | 1 |

---

### 6.9 검증 결과

| 항목 | 결과 |
| --- | --- |
| Tdoc OP Cardinality | ✅ 데이터와 일치 |
| Tdoc DP Cardinality | ✅ 데이터와 일치 |
| CR 속성 | ✅ 데이터와 일치 |
| LS 속성 | ✅ 데이터와 일치 |
| Enumeration | ✅ 모든 값 확인 |
| Inverse Property | ✅ 역관계 일치 확인 |

## Step 7: 인스턴스 생성 명세

### 7.1 목적

> Step 4~6에서 정의한 클래스, 속성, 제약조건을 바탕으로 Tdoc_list 데이터에서 인스턴스를 생성하기 위한 구현 명세
> 

**입력**: TDoc_List_Meeting_RAN1_120_final_.xlsx (36개 컬럼, 1,674행)

**출력**: Knowledge Graph (RDF/OWL 또는 JSON-LD)

---

### 7.2 인스턴스 생성 개요

### 7.2.1 생성할 인스턴스 요약 (RAN1#84~#122b, 59개 미팅 기준)

| 클래스 | 인스턴스 수 | 소스 |
| --- | --- | --- |
| Meeting | 59 | 파일명 |
| Release | 13 | Release 컬럼 (Rel-8 ~ Rel-20) |
| Company | ~300 | Source 컬럼 (정규화 후) |
| Contact | 993 | Contact, Contact ID 컬럼 |
| WorkItem | 419 | Related WIs 컬럼 |
| AgendaItem | 1,335 | Agenda item 컬럼 |
| Spec | 85 | Spec 컬럼 |
| WorkingGroup | 118 | To, Cc 컬럼 |
| Tdoc (일반) | 105,412 | Type이 discussion, other, report, agenda, Work Plan, draft TR, draft TS, response, WID new, SID new, WI summary |
| CR | 10,544 | Type이 CR, draftCR, pCR |
| LS | 6,301 | Type이 LS out 또는 LS in |
| **총계** | **~125,000+** |  |

### 7.2.2 생성 순서

인스턴스 간 참조 관계로 인해 순서가 중요합니다.

| 순서 | 클래스 | 이유 |
| --- | --- | --- |
| 1 | Meeting, Release, Company, Contact, WorkItem, AgendaItem, Spec, WorkingGroup | 참조 대상 (의존성 없음) |
| 2 | Tdoc, CR, LS | 위 클래스들을 참조 |

---

### 7.3 클래스별 인스턴스 생성 명세

---

### 7.3.1 Meeting

| 항목 | 내용 |
| --- | --- |
| 소스 | 파일명 (TDoc_List_Meeting_RAN1_120_final_.xlsx) |
| ID | `meetingNumber` 원본 값 (예: RAN1#120, RAN1#101-e) |
| 인스턴스 수 | 59개 (RAN1#84 ~ RAN1#122b) |

| 속성 | 소스 | 변환 규칙 | 예시 |
| --- | --- | --- | --- |
| meetingNumber | 파일명에서 추출 | 원본 그대로 | "RAN1#101-e" |
| canonicalMeetingNumber | meetingNumber | `-e` suffix 제거 | "RAN1#101" |
| workingGroup | 파일명에서 추출 | `#` 앞부분 | "RAN1" |

**정규화 예시:**

| 파일명 | meetingNumber | canonicalMeetingNumber |
| --- | --- | --- |
| TDoc_List_Meeting_RAN1_101-e_final_.xlsx | RAN1#101-e | RAN1#101 |
| TDoc_List_Meeting_RAN1_112bis-e_final_.xlsx | RAN1#112bis-e | RAN1#112bis |
| TDoc_List_Meeting_RAN1_120_final_.xlsx | RAN1#120 | RAN1#120 |
| TDoc_List_Meeting_RAN1_100_final_.xlsx | RAN1#100 | RAN1#100 |
| TDoc_List_Meeting_RAN1_100-e_final_.xlsx | RAN1#100-e | RAN1#100 |

참고: RAN1#100과 RAN1#100-e는 동일한 canonicalMeetingNumber를 가지며, COVID-19로 인한 특수 케이스임 (Step 5 참조)

---

### 7.3.2 Release

| 항목 | 내용 |
| --- | --- |
| 소스 | Release 컬럼 (고유 값) |
| ID | Release 값 그대로 |
| 인스턴스 수 | 5개 |

| 속성 | 소스 | 예시 |
| --- | --- | --- |
| releaseName | Release 컬럼 | "Rel-19" |

실제 값

---

Rel-15, Rel-16, Rel-17, Rel-18, Rel-19

---

---

### 7.3.3 Company

| 항목 | 내용 |
| --- | --- |
| 소스 | Source 컬럼 (쉼표 분리 후 고유 값) |
| ID | 회사명 |
| 인스턴스 수 | 166개 |

| 속성 | 소스 | 예시 |
| --- | --- | --- |
| companyName | Source에서 추출 | "Samsung" |

---

### 7.3.4 Contact

| 항목 | 내용 |
| --- | --- |
| 소스 | Contact, Contact ID 컬럼 |
| ID | Contact ID 값 |
| 인스턴스 수 | 209개 |

| 속성 | 소스 | 예시 |
| --- | --- | --- |
| contactName | Contact 컬럼 | "Patrick Merias" |
| contactId | Contact ID 컬럼 | "52292" |

---

### 7.3.5 WorkItem

| 항목 | 내용 |
| --- | --- |
| 소스 | Related WIs 컬럼 (쉼표 분리 후 고유 값) |
| ID | Work Item 코드 |
| 인스턴스 수 | 67개 |

| 속성 | 소스 | 예시 |
| --- | --- | --- |
| workItemCode | Related WIs에서 추출 | "NR_MIMO_Ph5-Core" |

---

### 7.3.6 AgendaItem

| 항목 | 내용 |
| --- | --- |
| 소스 | Agenda item, Agenda item description 컬럼 |
| ID | Agenda item 번호 |
| 인스턴스 수 | 64개 |

| 속성 | 소스 | 예시 |
| --- | --- | --- |
| agendaNumber | Agenda item 컬럼 | "9.1" |
| agendaDescription | Agenda item description 컬럼 | "AI/ML for NR Air Interface" |

---

### 7.3.7 Spec

| 항목 | 내용 |
| --- | --- |
| 소스 | Spec, Version 컬럼 |
| ID | Spec 번호 (문자열) |
| 인스턴스 수 | 7개 |

| 속성 | 소스 | 예시 |
| --- | --- | --- |
| specNumber | Spec 컬럼 | "38.212" |
| specVersion | Version 컬럼 (optional) | "18.5.0" |

실제 값

---

36.213, 38.211, 38.212, 38.213, 38.214, 38.215, 38.901

---

---

### 7.3.8 WorkingGroup

| 항목 | 내용 |
| --- | --- |
| 소스 | To, Cc 컬럼 (쉼표 분리 후 고유 값) |
| ID | WG 이름 |
| 인스턴스 수 | 10개 |

| 속성 | 소스 | 예시 |
| --- | --- | --- |
| wgName | To, Cc에서 추출 | "RAN1" |

실제 값

---

RAN, RAN1, RAN2, RAN3, RAN4, RAN5, SA, SA2, SA3, SA5

---

---

### 7.3.9 Tdoc (일반)

| 항목 | 내용 |
| --- | --- |
| 조건 | Type이 discussion, other, report, agenda, Work Plan |
| ID | TDoc 컬럼 값 |
| 인스턴스 수 | 1,457건 |

**속성 매핑**

| 속성 | 소스 컬럼 | 필수 |
| --- | --- | --- |
| tdocNumber | TDoc | ✅ |
| title | Title | ✅ |
| abstract | Abstract | ❌ |
| type | Type | ✅ |
| status | TDoc Status | ✅ |
| for | For | ❌ |
| reservationDate | Reservation date | ✅ |
| uploadedDate | Uploaded | ❌ |
| secretaryRemarks | Secretary Remarks | ❌ |

**관계 매핑**

| 속성 | 소스 컬럼 | 대상 클래스 | 필수 |
| --- | --- | --- | --- |
| submittedBy | Source | Company | ✅ |
| hasContact | Contact ID | Contact | ✅ |
| relatedTo | Related WIs | WorkItem | ❌ |
| belongsTo | Agenda item | AgendaItem | ✅ |
| targetRelease | Release | Release | ❌ |
| presentedAt | (파일명) | Meeting | ✅ |
| isRevisionOf | Is revision of | Tdoc | ❌ |
| revisedTo | Revised to | Tdoc | ❌ |
| replyTo | Reply to | Tdoc | ❌ |
| replyIn | Reply in | Tdoc | ❌ |

---

### 7.3.10 CR (Tdoc 하위 클래스)

| 항목 | 내용 |
| --- | --- |
| 조건 | Type이 CR 또는 draftCR |
| ID | TDoc 컬럼 값 |
| 상속 | Tdoc의 모든 속성/관계 |
| 인스턴스 수 | 80건 (CR 19 + draftCR 61) |

**추가 속성 매핑**

| 속성 | 소스 컬럼 | 필수 |
| --- | --- | --- |
| crNumber | CR | ❌ |
| crCategory | CR category | ❌ |
| clausesAffected | Clauses Affected | ❌ |
| tsgCRPack | TSG CR Pack | ❌ |
| affectsUICC | UICC | ❌ |
| affectsME | ME | ❌ |
| affectsRAN | RAN | ❌ |
| affectsCN | CN | ❌ |

**추가 관계 매핑**

| 속성 | 소스 컬럼 | 대상 클래스 | 필수 |
| --- | --- | --- | --- |
| modifies | Spec | Spec | ✅ |

---

### 7.3.11 LS (Tdoc 하위 클래스)

| 항목 | 내용 |
| --- | --- |
| 조건 | Type이 LS out 또는 LS in |
| ID | TDoc 컬럼 값 |
| 상속 | Tdoc의 모든 속성/관계 |
| 인스턴스 수 | 137건 (out 105 + in 32) |

**추가 속성 매핑**

| 속성 | 소스 컬럼 | 필수 |
| --- | --- | --- |
| direction | Type에서 추출 ("in" 또는 "out") | ✅ |

**추가 관계 매핑**

| 속성 | 소스 컬럼 | 대상 클래스 | 필수 |
| --- | --- | --- | --- |
| sentTo | To | WorkingGroup | ✅ |
| ccTo | Cc | WorkingGroup | ❌ |
| originalLS | Original LS | Tdoc (외부) | ❌ |

---

### 7.4 데이터 변환 규칙

### 7.4.1 복합 값 처리

| 컬럼 | 처리 | 결과 |
| --- | --- | --- |
| Source | 쉼표(,) 분리, trim | 복수 Company 참조 |
| Related WIs | 쉼표(,) 분리, trim | 복수 WorkItem 참조 |
| To | 쉼표(,) 분리, trim | 복수 WorkingGroup 참조 |
| Cc | 쉼표(,) 분리, trim | 복수 WorkingGroup 참조 |

### 7.4.2 타입 변환

| 컬럼 | 원본 타입 | 변환 |
| --- | --- | --- |
| Spec | float (38.212) | 문자열 "38.212" |
| CR | float (693.0) | 문자열 "693" |
| Reservation date | 문자열 "M/D/YYYY H:MM:SS AM/PM" | ISO 8601 |
| Uploaded | Timestamp | ISO 8601 |
| UICC, ME, RAN, CN | Boolean | 그대로 |

### 7.4.3 클래스 판별

### 7.4.3 클래스 판별

| Type 값 | 클래스 |
| --- | --- |
| CR, draftCR, pCR | CR |
| LS out, LS in | LS |
| discussion, other, report, agenda, Work Plan, draft TR, draft TS, response, WID new, SID new, WI summary | Tdoc |

---

### 7.5 참조 무결성 처리

### 7.5.1 내부 참조 (같은 파일 내)

| 속성 | 전체 | 내부 | 외부 |
| --- | --- | --- | --- |
| isRevisionOf | 74건 | 74건 | 0건 |
| revisedTo | 77건 | 74건 | 3건 |
| replyIn | 13건 | 11건 | 2건 |

### 7.5.2 외부 참조 (다른 회의/WG 문서)

| 속성 | 전체 | 내부 | 외부 | 설명 |
| --- | --- | --- | --- | --- |
| replyTo | 89건 | 0건 | 89건 | 모두 이전 회의 문서 |
| originalLS | 32건 | 0건 | 32건 | 모두 다른 WG 문서 |

**처리 방안**: 외부 참조는 문자열로 저장, 향후 해당 데이터 추가 시 연결

---

### 7.6 데이터 정규화 전략

인스턴스 생성 전, 데이터 품질을 보장하기 위해 **사전 정규화**를 수행합니다.

### 7.6.1 정규화 필요 항목

| 항목 | 정규화 필요 | 이유 |
| --- | --- | --- |
| **Company** | ✅ 필수 | 대소문자, 변형, 역할 포함, 괄호 이슈 |
| WorkItem | ❌ | 일관됨 |
| WorkingGroup | ❌ | 일관됨 |
| Enumeration | ❌ | 일관됨 |
| Spec | ❌ | 일관됨 |
| Agenda | ❌ | 일관됨 |
| Contact | ❌ | 일관됨 |

### 7.6.2 Company 정규화 이슈

| 이슈 유형 | 예시 |
| --- | --- |
| 대소문자 불일치 | vivo, Vivo, VIVO |
| 회사명 변형 | ZTE, ZTE Corporation |
| 약어 | LG Electronics, LGE |
| 역할 포함 | Moderator (Samsung), Rapporteur (Huawei) |
| 괄호 내 쉼표 | "Moderator (NTT DOCOMO, INC.)" → 잘못 분리됨 |
| 오타/마침표 | CAICT., CATT) |

### 7.6.3 정규화 파이프라인

```
[1단계] 괄호 내 쉼표 처리 (정규식)
        "Moderator (NTT DOCOMO, INC.)" → 분리 안 함
           │
           ▼
[2단계] 역할 분리 (정규식)
        "Moderator (Samsung)" → 역할: Moderator, 회사: Samsung
           │
           ▼
[3단계] 고유 회사명 추출
           │
           ▼
[4단계] LLM 정규화 (1~2회 호출)
        "이 회사명들을 정규화해줘"
           │
           ▼
[5단계] company_aliases.json 저장

```

### 7.6.4 정규화 사전 형식

**company_aliases.json**

```json
{
  "Samsung": ["Samsung", "Samsung Electronics", "SEC", "BEIJING SAMSUNG TELECOM R&D"],
  "Huawei": ["Huawei", "HW", "Huawei Technologies", "HiSilicon"],
  "ZTE": ["ZTE", "ZTE Corporation"],
  "vivo": ["vivo", "Vivo", "VIVO"],
  "ASUS": ["ASUSTEK", "ASUSTeK", "ASUSTek"],
  "LG": ["LG Electronics", "LGE"],
  "NTT DOCOMO": ["NTT DOCOMO", "NTT DOCOMO, INC."],
  "InterDigital": ["InterDigital", "InterDigital, Inc."]
}

```

### 7.6.5 역할 분리 규칙

| 원본 | 역할 | 회사 |
| --- | --- | --- |
| Moderator (Samsung) | Moderator | Samsung |
| Rapporteur (Huawei) | Rapporteur | Huawei |
| Ad-Hoc Chair (Ericsson) | Ad-Hoc Chair | Ericsson |
| RAN1 Chair | RAN1 Chair | (역할만, 회사 없음) |

**참고**: 역할 정보는 Tdoc의 `submittedBy` 관계에서 별도 속성으로 저장하거나, 향후 확장 시 활용

### 7.7 인스턴스 생성 파이프라인

인스턴스 생성의 정확성을 보장하기 위해 **4단계 파이프라인**을 적용합니다.

```
[원본 데이터]
     │
     ├──────────────────┬──────────────────┐
     ▼                  ▼                  │
[1. 정규식 추출]   [2. LLM 추출]           │
     │                  │                  │
     └────────┬─────────┘                  │
              ▼                            │
       [3. LLM 종합 판단]                  │
              │                            │
              ▼                            │
       [인스턴스 생성]                     │
              │                            │
              ▼                            ▼
       [4. 원본 대조 검증] ◄───────────────┘
              │
              ▼
       [검증 완료 / 오류 리포트]

```

---

### 7.7.1 1단계: 정규식 추출

| 역할 | 명확한 패턴 기반 데이터 추출 |
| --- | --- |
| 장점 | 빠름, 일관성, 저비용 |
| 한계 | 예외 케이스 놓침, 문맥 이해 불가 |

**처리 대상**

| 항목 | 규칙 |
| --- | --- |
| 파일명 → Meeting | 정규식 패턴 매칭 |
| 복합 값 분리 | 쉼표(,) 분리, trim |
| 타입 변환 | float → string, DateTime 변환 |
| 클래스 판별 | Type 값 기반 분기 |

---

### 7.7.2 2단계: LLM 추출

| 역할 | 문맥 기반 데이터 추출 및 정규화 |
| --- | --- |
| 장점 | 애매한 케이스 처리, 오타 수정, 약어 해석 |
| 한계 | 비용, 속도 |

**처리 대상**

| 항목 | LLM 역할 |
| --- | --- |
| Company 정규화 | 동일 회사 판단, 약어 해석, 오타 수정 |
| 외부 참조 추론 | 어느 회의/WG 문서인지 추론 |
| 데이터 일관성 | 같은 ID에 다른 값 → 오류 감지 |
| 정규식 실패 | 패턴 매칭 실패 시 추론 |

---

### 7.7.3 3단계: LLM 종합 판단

| 역할 | 두 결과 비교, 충돌 해결, 최종 결과 생성 |
| --- | --- |

**처리 로직**

| 상황 | 처리 |
| --- | --- |
| 정규식 = LLM | 그대로 채택 |
| 정규식만 있음 | 정규식 채택 |
| LLM만 있음 | LLM 채택 |
| 충돌 | LLM이 문맥 고려하여 판단, 근거 기록 |

---

### 7.7.4 4단계: 원본 대조 검증

| 역할 | 누락/오류 검출, 무결성 확인 |
| --- | --- |

**검증 항목**

| 검증 | 기대 결과 |
| --- | --- |
| 행 수 일치 | Tdoc + CR + LS = 1,674 |
| 클래스 분류 | CR 80, LS 137, Tdoc 1,457 |
| 필수 속성 | 모두 존재 |
| 내부 참조 | 모두 유효 |
| 외부 참조 | 문자열로 기록 (121건) |
| Enum 값 | 정의된 범위 내 |

---

### 7.8 출력 형식

| 형식 | 용도 |
| --- | --- |
| JSON-LD (권장) | 웹 표준, API 응답 |
| RDF/Turtle | SPARQL 쿼리, Triple Store |
| RDF/XML | 레거시 시스템 연동 |

---

### 7.9 네임스페이스 정의

| Prefix | URI | 용도 |
| --- | --- | --- |
| tdoc | http://3gpp.org/ontology/tdoc# | 3GPP Tdoc Ontology |
| dc | http://purl.org/dc/elements/1.1/ | Dublin Core |
| foaf | http://xmlns.com/foaf/0.1/ | FOAF |
| xsd | http://www.w3.org/2001/XMLSchema# | 데이터 타입 |

---

### 7.10 검증 리포트 형식

```
=== 인스턴스 생성 검증 결과 ===
상태: PASS / FAIL

[1] 인스턴스 수 검증
  - Tdoc: 1,457건 ✅
  - CR: 80건 ✅
  - LS: 137건 ✅
  - 총합: 1,674건 ✅

[2] 필수 속성 검증
  - 누락: 0건 ✅

[3] 참조 무결성 검증
  - 내부 참조 오류: 0건 ✅
  - 외부 참조 기록: 121건 ✅

[4] Enum 유효성 검증
  - 유효하지 않은 값: 0건 ✅

[5] 오류 목록
  (오류 있으면 상세 기록)

```

---