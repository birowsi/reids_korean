import sys
import subprocess
import os
import hashlib
import json

def get_sha256(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def build_patch(original_rom, modified_rom, patch_name):
    if not os.path.exists("xdelta3.exe"):
        print("오류: xdelta3.exe 파일이 같은 폴더에 필요합니다.")
        return
        
    print("패치 파일을 생성 중입니다...")
    # xdelta3 명령어: xdelta3 -e -s [원본] [수정본] [패치파일]
    cmd = ["xdelta3.exe", "-e", "-s", original_rom, modified_rom, patch_name]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        print("패치 생성 실패!")
        print(result.stderr.decode('utf-8', errors='ignore'))
        return

    # 무결성 검증을 위한 수정본 해시값 저장
    print("메타데이터(무결성 검증용)를 생성 중입니다...")
    target_hash = get_sha256(modified_rom)
    metadata = {
        "target_hash": target_hash
    }
    with open(patch_name + ".meta", "w", encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)
        
    print(f"패치 생성 완료: {patch_name}")
    print(f"메타데이터 생성 완료: {patch_name}.meta")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("사용법: python builder.py <원본_ROM> <수정된_ROM> <생성할_패치이름>")
        sys.exit(1)
    
    build_patch(sys.argv[1], sys.argv[2], sys.argv[3])
