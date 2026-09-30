# 에반게리온 아야나미 육성계획 DS 한글 패치 프로젝트

닌텐도 DS용 「신세기 에반게리온 - 아야나미 육성계획 DS with 아스카 보완계획」의 비공식 한국어 롬 해킹 및 번역 프로젝트입니다.

## 요구 사항
- Windows OS
- Python 3.10+
- `ndstool` (롬 언패킹/리빌드용)
- `xdelta3` (바이너리 패치 생성용)
- .NET Framework (패처 컴파일용)

## 빌드 가이드 (개발자용)

이 레포지토리는 배포용 패치 파일이 아닌, 패치 생성에 필요한 소스 코드와 번역 스크립트 데이터를 포함하고 있습니다. 소스에서 직접 패치를 빌드하려면 아래 과정을 따르세요.

### 1. 초기 설정
루트 디렉토리에 원본 일본어 롬 파일을 `original.nds` 이름으로 배치합니다.

파이썬 의존성 패키지를 설치합니다:
```bash
pip install cryptography
```

### 2. 텍스트 데이터 패킹
수정된 번역 데이터(`translation_work.csv`)를 게임 내 스크립트(`.scd`)에 맞게 변환하고 주입합니다.
```bash
python import_from_csv.py
python text_packer.py
python validate_project.py
```

### 3. 롬 리빌드
번역된 폰트와 변경된 에셋을 포함하여 최종 롬(`rei.nds`)을 리빌드합니다.
빌드 스크립트는 작업용 `*.bak` 파일을 임시 스테이징 디렉터리에서 자동으로 제외합니다.
```bash
python build_rom.py
```

### 4. 배포용 패치 생성 및 암호화
원본 롬과 수정된 롬을 비교하여 `.xdelta` 패치를 생성하고, 배포 전용 패처에서 읽을 수 있도록 AES 암호화된 `.dat` 파일로 변환합니다.
```bash
# xdelta 패치 생성
python builder.py original.nds rei.nds korean_patch_v6.xdelta

# dat 암호화
python encrypt_patch.py
```

### 5. 전용 패처 컴파일
기본 내장된 C# 컴파일러를 이용해 배포용 패처 실행 파일을 빌드합니다.
```cmd
compile_patcher.bat
```
빌드가 완료되면 `Korean_Patcher.exe`, `korean_patch_v6.dat`, `xdelta3.exe`,
`PATCH_README.txt` 파일을 함께 압축하여 배포합니다. 원본 ROM은 포함하지 않습니다.

패처는 실행 파일 폴더에서 보조 파일을 찾고 결과 `rei.nds`도 그 폴더에 생성합니다.
입력과 출력 경로가 같으면 거부하며, 임시 결과를 SHA-256 검증한 뒤에만 기존 결과를
교체합니다. 실패한 패치 작업으로 원본이나 기존 결과 ROM을 덮어쓰지 않습니다.

## 릴리스 전 필수 검증

아래 명령은 미번역 문자열, 제어 문자열 훼손, 지원하지 않는 문자, 바이트 초과,
CSV/JSONL 동기화, 한국식 계급, SCD 범위 밖 변경을 모두 검사합니다.
이번 검수로 보정한 문장은 원문 표시 글자수 이내인지도 검사합니다.
기존 전체 번역의 단순 글자수 일치나 모든 화면의 표시 폭을 보증하는 검사는 아닙니다.
오류가 하나라도 있으면 릴리스하지 마세요.

```bash
python import_from_csv.py
python text_packer.py
python validate_project.py
python build_rom.py
python fix_crc.py rei.nds
```

검수 보정 재적용(자동 잘라내기 없음):
```bash
python repair_translation_review.py --write
```

패치와 실행 파일을 다시 만든 뒤 사용자용 패처 회귀 테스트:
```bash
python test_release_safety.py
```
정상 적용/기존 결과 교체, 다른 작업 폴더·한글 경로, 입력=출력,
잘못된 ROM/PIN/패치 데이터, 디코더 실패, 결과 해시 불일치 시 보존을 검사합니다.
테스트에는 `cryptography`와 Python 3.11+가 필요합니다. 실제 플레이 QA를 대체하지 않습니다.

## 크레딧 및 라이선스
- 게임 내 한글 폰트는 [갈무리(Galmuri)](https://galmuri.quiple.dev/) 폰트를 변환하여 사용했습니다. (SIL Open Font License)
- 본 프로젝트는 상업적 목적으로 배포되거나 사용될 수 없습니다.
