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
```

### 3. 롬 리빌드
번역된 폰트 파일(`font.nftr`)과 변경된 에셋들을 포함하여 `ndstool`로 최종 롬(`rei.nds`)을 리빌드합니다.
```bash
ndstool.exe -c rei.nds -9 arm9.bin -7 arm7.bin -y9 y9.bin -y7 y7.bin -d data -y overlay -t banner.bin -h header.bin
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
빌드가 완료되면 `Korean_Patcher.exe`, `korean_patch_v6.dat`, `xdelta3.exe` 파일을 함께 압축하여 배포합니다.

## 크레딧 및 라이선스
- 게임 내 한글 폰트는 [갈무리(Galmuri)](https://galmuri.quiple.dev/) 폰트를 변환하여 사용했습니다. (SIL Open Font License)
- 본 프로젝트는 상업적 목적으로 배포되거나 사용될 수 없습니다.
