# 재빌드

## 준비물

- 원본 CPK 4개 (PCSE00595 복호화 게임 폴더의 `data/VITA/`): `partition_op_game_vita.cpk`, `partition_op_battle_vita.cpk`, `partition_op_progress_vita.cpk`, `partition_op_character_vita.cpk` (해시는 `release_manifest.json`)
- Python 3.13, `Pillow`, `numpy`, `opencv-python`, `fontTools`
- 글꼴: `docs/FONT_CREDITS.md`의 7개를 저장소 최상위 폴더에
- xdelta3 (배포 파일을 만들 때만)

## 빌드

원본 CPK 4개를 `work/base/`에 넣고 저장소 폴더에서 실행합니다.

```powershell
python tools/prepare.py
python tools/build.py
```

`prepare.py`는 원본에서 영어 문장을 읽어 `text/ko.json`과 연결하고, `text/images/`를 `work/`에 복사합니다. `build.py`는 결과 CPK 4개를 `out/`에 만듭니다(`--out <폴더>`로 바꿀 수 있음). 결과의 SHA-256을 `release_manifest.json`의 `output_sha256`과 비교하세요. 같은 원본과 글꼴이면 바이트 단위로 같은 결과가 나옵니다.

## 배포 파일

```powershell
xdelta3 -e -0 -S none -A -s work\base\partition_op_game_vita.cpk out\partition_op_game_vita.cpk J-Stars_Victory_VS_Plus_Vita_KO_v1.0_game.xdelta
```

`battle`·`progress`·`character`도 같은 방법으로 만듭니다.

## 번역 수정

- `text/ko.json`: `{"<내부 pak>/<텍스트 파일>": "한국어"}`. `\n`은 줄바꿈입니다. `<...>` 형식 태그는 그대로 둡니다.
- 원문을 보려면 `python -c "import sys; sys.path.insert(0,'tools'); import srcmap; print(srcmap.collect('work/base')['<키>'])"`처럼 읽습니다.
- 새 한글 글자는 빌드 때 자동으로 글꼴에 들어갑니다. 원문 폭을 넘는 긴 문장은 자동으로 줄을 다시 나누며, 넘친 목록은 `work/overflow.txt`에 남습니다.
- 그림 글자: `text/images/<묶음>/texts_*.json`의 `ko`를 고칩니다. 키는 같은 폴더 `inventory.json`의 순번입니다. `mode: "alpha"`는 투명 배경 글자, `group`·`layer: "glow"`는 같은 글자의 빛 번짐 층, `box`는 지정 영역만 다시 쓰기입니다. 로딩 TIPS 스크린샷 속 설명은 `tools/tipcaps.py`에 위치와 함께 적혀 있습니다.

## 에뮬레이터 확인

`tools/emu.py`는 저장소 옆 `emu/`에 설치한 Vita3K를 백그라운드로 띄우고 키 입력과 스크린샷(F12 단축키)을 보냅니다. `start`, `key x _2 Hx:0.3`, `shot out.png`, `stop` 순서로 씁니다. 결과 CPK를 `emu/fs/ux0/app/PCSE00595/data/VITA/`에 넣고 확인합니다.
