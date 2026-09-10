# 영어 학습 데이터 스키마

## 저장 형식

- **정규화 데이터**: `data/vocab.jsonl` — 단어 1개 = 1줄(JSON). 검색·집계·diff에 유리.
- **원본 보관**: `data/raw/` — 붙여넣은 원문 그대로. 파싱 실수 시 되돌릴 근거.
- **읽기용 뷰**: `views/` — jsonl에서 생성하는 마크다운(단어장, 주제별, 복습 목록). 손으로 고치지 않음.

단일 소스는 항상 `data/vocab.jsonl`. 나머지는 파생물.

## 필드 정의

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `id` | string | ✅ | 안정적 식별자. `표제어-품사` 소문자 케밥 (예: `run-into-v`) |
| `word` | string | ✅ | 표제어. 구동사·숙어도 그대로 (예: `run into`) |
| `pos` | string | ✅ | `n` `v` `adj` `adv` `phr` `idiom` `phrasal_verb` 중 하나 |
| `meaning_ko` | string | ✅ | 한국어 뜻. 여러 뜻은 `;`로 구분 |
| `meaning_en` | string | | 영영 정의. 뉘앙스 구분에 필요 |
| `ipa` | string | | 발음기호 |
| `level` | string | | CEFR: `A1`~`C2` |
| `register` | string | | `formal` `neutral` `informal` `slang` `business` |
| `sentences` | array | ✅ | 아래 문장 객체 배열. 최소 1개 |
| `collocations` | string[] | | 자주 붙는 조합 (예: `heavily rely on`) |
| `synonyms` | string[] | | 유의어 |
| `confusables` | string[] | | 헷갈리는 단어 + 차이점 메모 |
| `tags` | string[] | | 주제 분류 (예: `business`, `daily`, `tech`, `email`) |
| `source` | string | | 어디서 봤는지 (책/영상/회의 등) |
| `added_at` | string | ✅ | `YYYY-MM-DD` |
| `srs` | object | ✅ | 복습 상태. 아래 참조 |

### 문장 객체 (`sentences[]`)

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `en` | string | ✅ | 추천 문장 |
| `ko` | string | ✅ | 한국어 해석. **모든 예문에 반드시 포함** |
| `note` | string | | 왜 이 문장인지 / 문법 포인트 |
| `source` | string | | 출처 |

### 복습 상태 (`srs`)

| 필드 | 타입 | 설명 |
|---|---|---|
| `status` | string | `new` → `learning` → `review` → `known` |
| `reps` | number | 성공 복습 횟수 |
| `lapses` | number | 틀린 횟수 |
| `interval_days` | number | 다음 복습까지 간격 |
| `due` | string | `YYYY-MM-DD`. 이 날짜 이전이면 복습 대상 |
| `last_reviewed` | string | `YYYY-MM-DD` 또는 `null` |

## 예시 (1줄)

```json
{"id":"run-into-phrasal_verb","word":"run into","pos":"phrasal_verb","meaning_ko":"우연히 마주치다; (문제에) 부딪히다","meaning_en":"to meet someone unexpectedly, or to encounter a problem","ipa":"/rʌn ˈɪntuː/","level":"B1","register":"neutral","sentences":[{"en":"I ran into an old colleague at the conference.","ko":"학회에서 옛 동료를 우연히 만났다.","note":"사람 목적어 = 우연히 마주치다"},{"en":"We ran into a few issues during the migration.","ko":"마이그레이션 중에 몇 가지 문제에 부딪혔다.","note":"issue/problem/trouble 목적어 = 문제에 봉착"}],"collocations":["run into trouble","run into a problem"],"synonyms":["bump into","encounter"],"confusables":["run over"],"tags":["daily","work"],"source":"예시","added_at":"2026-08-02","srs":{"status":"new","reps":0,"lapses":0,"interval_days":0,"due":"2026-08-02","last_reviewed":null}}
```

## 입력 규칙

- **모든 항목은 예문 + 한국어 해석을 반드시 가진다.** 뜻만 있고 예문이 없는 항목은 등록하지 않음. `scripts/validate.py`가 강제.
- 데이터를 넣을 때는 **원본을 그대로** 주면 됨. 표 형식, 메모, 두서없는 목록 모두 가능.
- 정규화 시 원본은 `data/raw/YYYY-MM-DD-<설명>.txt`로 먼저 보관.
- 뜻·문장이 비어 있으면 임의로 채우지 않고 `needs_review` 태그를 붙여 표시.
- 중복 표제어는 `pos`가 다르면 별도 항목, 같으면 `sentences` 병합.
