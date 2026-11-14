# J스타즈 빅토리 VS+ PS Vita 한글패치

PS Vita 북미판 **J-Stars Victory VS+ (PCSE00595)**용 비공식 한국어 패치입니다. J 어드벤처 스토리 대사, 메뉴·옵션, 캐릭터·기술 설명, 퀘스트·아이템·카드·칭호, 아케이드·빅토리 로드 문장까지 게임 안의 영어 문장 **17,534개 전체**를 한국어로 바꿨습니다. 게임 글꼴에 한글 1,235자를 넣고, 메뉴 제목·버튼·로딩 TIPS·캐릭터 이름 등 그림 글자 **1,472장**을 한글로 다시 그렸습니다. 현재 배포판은 **v1.0 (2026-11-15)**입니다.

[패치 다운로드](https://github.com/snake759494/j-stars-victory-vs-plus-vita-korean-patch/releases/latest) · [기술 설명](docs/TECHNICAL.md) · [재빌드](docs/BUILD.md) · [용어집](docs/GLOSSARY.md) · [변경 기록](CHANGELOG.md) · [권리 안내](RIGHTS.md)

릴리즈 첨부 파일은 게임 데이터 파일 4개에 각각 대응하는 xdelta 4개입니다. 저장소에는 제작 소스와 한국어 번역만 공개합니다. 원본·완성 게임 파일, 추출한 게임 데이터·그림, 영어 원문, 글꼴 파일, 외부 실행 파일은 포함하지 않습니다. GitHub가 자동으로 만드는 Source code ZIP/TAR는 저장소 소스를 압축한 것이며 게임 파일이 아닙니다.

## 게임 소개 및 대상 버전

『J스타즈 빅토리 VS+』는 스파이크 춘소프트가 개발하고 반다이 남코 엔터테인먼트가 낸 주간 소년 점프 45주년 기념 크로스오버 대전 액션 게임입니다. 『드래곤볼』『원피스』『나루토』『블리치』『헌터×헌터』 등 점프 작품의 캐릭터들이 2대2 팀 배틀을 벌이며, 배를 타고 점프 월드를 모험하는 「J 어드벤처」 모드가 있습니다. 2015년 북미·유럽에 PS Vita·PS3·PS4로 나왔습니다.

이 패치는 **PS Vita 북미판(PCSE00595)의 `data/VITA/` 폴더에 있는 CPK 4개**에 적용합니다. 복호화된 게임 폴더(`ux0:app/PCSE00595/`)에 있는 파일이어야 합니다. 파일 이름보다 아래 크기와 해시가 일치하는지가 중요합니다.

## 적용할 원본

| 파일 | 크기 | MD5 | SHA-256 |
| --- | --- | --- | --- |
| 원본 `partition_op_game_vita.cpk` | 6,028,032 B | `e338ef4d0143441fdd2841a30f4b49ce` | `2ec7d812251564f3d70dc88353490456ab7c5d730ec5140ec818252e44b5b20d` |
| 원본 `partition_op_battle_vita.cpk` | 37,325,896 B | `98ad0ca3504cf3b83e9b396a5ff157ac` | `18e14c1df5936c8ff9ea382db440276cd2c05f6585d2f9165ac24fae1a8ab975` |
| 원본 `partition_op_progress_vita.cpk` | 508,703,664 B | `df5dcad6fcd13a48a4994028f81e26b3` | `129d124747edfe649760ea89c66ef16f81dbdce345edd4941b2adc2e8afb64dc` |
| 원본 `partition_op_character_vita.cpk` | 413,120,528 B | `26c8052d7a4bde77606e3bc194c53b2b` | `f75a1c87caee3ac30b3d7a6d70e2f2f367042f116b243e8a6fca29265d88f090` |
| 결과 `partition_op_game_vita.cpk` | 8,806,400 B | `73038301a2a4405812ea1b264be87ee9` | `fde147a1e9039b1dc04aa9e04c2ac71ecaeb68ed9e41bf973027204151ebc333` |
| 결과 `partition_op_battle_vita.cpk` | 46,864,384 B | `6e9aeef2486959d6b3aba20b3689dc68` | `2b6837605b2e0a4cff60399d8c188661ee66b5d3918714e974e976db053c5b43` |
| 결과 `partition_op_progress_vita.cpk` | 661,522,432 B | `27733b48749388eceb1124b6cdc583af` | `3e9c8cbb09bbf1e47ff633bd7e13c2065a4014e8dc83a87f21f461118e1fa364` |
| 결과 `partition_op_character_vita.cpk` | 469,581,824 B | `7be1d948cfddcb8635a9f576545fe911` | `f9caf75ec5155b9fa79b552cd103824cd457af826a4c8fc7dbe907d9d119f09c` |
| `J-Stars_Victory_VS_Plus_Vita_KO_v1.0_game.xdelta` | 1,912,329 B | `8a5e95f78c37e0e80d79de0f6dec4a11` | `5c3b01f44b2cc517d50c645ef9420bd1c264781029c95582482d636fd306f792` |
| `J-Stars_Victory_VS_Plus_Vita_KO_v1.0_battle.xdelta` | 5,166,805 B | `85aacccb516a83b611ab6484e40c443a` | `df251abc9a082dc6ed3c009c9081e4b6b76c98a452a980fecdf0cc87da146223` |
| `J-Stars_Victory_VS_Plus_Vita_KO_v1.0_progress.xdelta` | 76,300,452 B | `f26455736a8061edca4cb2fddae6c95b` | `15894eee4f12a5c08a125c59ec9bfda4fd14a4209b50af625e949dbcc48b561a` |
| `J-Stars_Victory_VS_Plus_Vita_KO_v1.0_character.xdelta` | 26,596,306 B | `328fd26d54c06b33f701904c52163443` | `9765992fd6cb8b7b4b1b1f126e33d8758eaabc06a11752f648cfafb93401624f` |

SHA-1은 [release_manifest.json](release_manifest.json)에 있습니다. 원본 게임 파일은 사용자가 직접 준비해야 합니다. `eboot.bin`과 그 밖의 파일은 바꾸지 않습니다.

## 패치 적용 방법

### Windows에서 원본 확인

```powershell
Get-FileHash -Algorithm MD5 -LiteralPath '.\partition_op_game_vita.cpk'
```

나머지 3개도 같은 방법으로 확인합니다. 위 표와 다르면 적용을 중단하세요.

### xdelta UI 사용

1. 릴리즈에서 xdelta 4개를 받습니다.
2. xdelta3 패치를 지원하는 도구에서 **Apply Patch** 기능을 엽니다.
3. 파일마다 **Patch**에는 xdelta 파일을, **Source File**에는 해시가 일치하는 같은 이름의 원본 CPK를 선택합니다(`..._game.xdelta` → `partition_op_game_vita.cpk`).
4. **Output File**에는 새 파일 이름을 지정합니다(예: `partition_op_game_vita_ko.cpk`). 다 만든 뒤 원래 이름으로 바꿔 아래 위치에 넣습니다.

xdelta는 호환성을 위해 압축·2차 압축·파일 경로 헤더 없이 만들었습니다. xdelta 자체는 [공식 프로젝트](https://github.com/jmacd/xdelta)를 참고하세요.

### 명령줄 사용

```powershell
.\xdelta3.exe -d -s '.\partition_op_game_vita.cpk' '.\J-Stars_Victory_VS_Plus_Vita_KO_v1.0_game.xdelta' '.\ko\partition_op_game_vita.cpk'
.\xdelta3.exe -d -s '.\partition_op_battle_vita.cpk' '.\J-Stars_Victory_VS_Plus_Vita_KO_v1.0_battle.xdelta' '.\ko\partition_op_battle_vita.cpk'
.\xdelta3.exe -d -s '.\partition_op_progress_vita.cpk' '.\J-Stars_Victory_VS_Plus_Vita_KO_v1.0_progress.xdelta' '.\ko\partition_op_progress_vita.cpk'
.\xdelta3.exe -d -s '.\partition_op_character_vita.cpk' '.\J-Stars_Victory_VS_Plus_Vita_KO_v1.0_character.xdelta' '.\ko\partition_op_character_vita.cpk'
```

해시를 자동으로 검사하는 도구도 있습니다. Python 3와 xdelta3가 필요하며, 원본 CPK 4개와 xdelta 4개가 있는 폴더를 지정하면 결과를 출력 폴더에 만듭니다. 같은 이름의 출력 파일이 이미 있으면 덮어쓰지 않습니다.

```powershell
python tools/apply_release.py --xdelta '.\xdelta3.exe' --source-dir '.\VITA' --patch-dir '.\patch' --output-dir '.\ko'
```

### 게임에 넣기

- **PS Vita 실기(rePatch, 권장)**: 결과 CPK 4개를 `ux0:rePatch/PCSE00595/data/VITA/`에 복사합니다. 원본 게임 폴더는 그대로 둡니다.
- **PS Vita 실기(직접 교체)**: `ux0:app/PCSE00595/data/VITA/`의 CPK 4개를 백업한 뒤 결과 파일로 덮어씁니다.
- **Vita3K**: 설치된 게임 폴더(`<Vita3K 데이터 폴더>/ux0/app/PCSE00595/data/VITA/`)의 CPK 4개를 결과 파일로 바꿉니다.

4개를 모두 바꿔야 합니다. 북미판이므로 **✕ 버튼이 결정, ○ 버튼이 취소**입니다. 세이브 데이터 형식은 바꾸지 않았습니다.

## 작업 내용과 범위

| 구분 | 작업량 및 내용 |
| --- | --- |
| 스토리 | J 어드벤처 대사·선택지·퀘스트·이벤트, 빅토리 로드·아케이드 대사와 장 설명 |
| 메뉴·시스템 | 메인 메뉴·옵션·캐릭터 선택·스테이지/BGM 선택·결과·확인창·세이브 메시지 |
| 데이터 | 캐릭터·기술·필살기 설명, 아이템·배·카드·칭호·갤러리·J 포인트 숍·도감 |
| 문장 | 영어 문장 **17,534개 전체**(텍스트 파일 36,724개) |
| 게임 글꼴 | `op_font_US_VITA`에 한글 **1,235자**와 기호 추가(나눔스퀘어네오 Rg) |
| 그림 글자 | 메뉴 제목·버튼·탭·라벨, 로딩 「로딩 중...」·「계속」, 로딩 TIPS 22장(제목·본문·스크린샷 속 설명), 캐릭터 이름(선택·VS·배틀·등장 연출), 파트너/장비 화면 라벨, 「파이트」 등 **1,472장** |

바꾼 파일은 원본 CPK 끝에 덧붙이고 목차만 고쳤습니다. 원본 데이터는 그대로 남으므로 문장 길이 제한이 없습니다. 자세한 내용은 [docs/TECHNICAL.md](docs/TECHNICAL.md)를 참고하세요.

### 번역 원칙

- 기계 번역 없이 영어 원문과 문맥을 보고 직접 번역했습니다.
- 인명·기술·지명은 각 작품의 국내 정식 표기를 따르고 한 가지로 통일했습니다([용어집](docs/GLOSSARY.md)). 예: 손오공, 루피, 나루토, 이치고, 에네르기파, 고무고무.
- 화면별 어미를 통일했습니다(확인창 「~습니다」, 설명문 「~한다」, 메뉴는 명사형). 캐릭터 대사는 원작 말투를 살렸습니다.

### 번역하지 않은 것

- 음성(일본어)
- 스태프롤
- 작품 로고, J-STARS 타이틀 로고
- 「Hits」「Burst!」「TAG-TEAM MELEE」 등 연출 효과 그림, 「OK」·「PRESS START」 버튼 표기
- 일부 TIPS 안에 들어 있는 작은 메뉴 스크린샷

## 알려진 한계

- 모든 장면을 게임으로 직접 플레이하며 확인하지는 못했습니다. Vita3K에서 타이틀·메인 메뉴·J 어드벤처 초반(대사·지도·퀘스트·아이템·배 화면)·프리 배틀(캐릭터 선택·스테이지 선택·VS 화면·로딩 TIPS·배틀 HUD·결과·재대전 메뉴)을 확인했습니다.
- 긴 한국어 문장 일부(약 200곳)는 원문 폭에 맞추기 어려워 줄바꿈을 조정했습니다. 상자 밖으로 넘치는 곳이 있으면 이슈로 알려 주세요.
- 온라인 대전 화면은 확인하지 못했습니다. 실기에서의 동작도 확인하지 못했습니다.

## 저장소 구성

| 경로 | 내용 |
| --- | --- |
| `tools/prepare.py` | 원본 CPK에서 원문을 읽어 `text/ko.json`과 연결하고 빌드 작업 폴더를 준비 |
| `tools/build.py` | 원본 CPK 4개에서 한글판을 빌드(텍스트 교체, 글꼴 생성, 그림 글자 재작성, CPK 덧붙이기) |
| `tools/` | 빌드·검증 도구(Python). `cpk.py` CPK 읽기, `scmp.py` `$CMP` 압축, `stpk.py`·`pakedit.py` KPTS 아카이브, `srd.py`·`dxt.py` SRD 텍스처(DXT1/DXT5/ARGB4444/BGRA, 스위즐), `fontbuild.py` SpFt 글꼴, `retext.py`·`tips.py`·`tipcaps.py`·`layers.py` 그림 글자 재작성, `srcmap.py` 원문 위치, `texdump.py`·`alltex.py`·`dumpmissing.py` 텍스처 조사, `emu.py` 에뮬레이터 조작, `apply_release.py` 해시 검사 후 적용 |
| `text/ko.json` | 번역. `<내부 pak>/<텍스트 파일>` → 한국어 |
| `text/images/` | 그림 글자 번역. 텍스처 목록(위치·크기·해시)과 텍스처별 한국어·글자 스타일 |
| `docs/` | 기술 설명, 재빌드 방법, 용어집, 글꼴 출처 |

권리 관련 내용은 [RIGHTS.md](RIGHTS.md)를 참고하세요.
