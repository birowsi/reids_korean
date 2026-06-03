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

def apply_patch(original_rom, patch_name, output_rom):
    if not os.path.exists("xdelta3.exe"):
        print("오류: xdelta3.exe 파일이 같은 폴더에 필요합니다.")
        return

    print("패치를 적용 중입니다...")
    # xdelta3 명령어: xdelta3 -d -s [원본] [패치파일] [결과파일]
    cmd = ["xdelta3.exe", "-d", "-s", original_rom, patch_name, output_rom]
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode != 0:
        print("패치 적용 실패!")
        print(result.stderr.decode('utf-8', errors='ignore'))
        return
        
    print("패치 적용이 완료되었습니다.")
    
    # 무결성 검증 (메타데이터가 있는 경우)
    meta_file = patch_name + ".meta"
    if os.path.exists(meta_file):
        print("무결성 검증을 시작합니다...")
        with open(meta_file, "r", encoding='utf-8') as f:
            metadata = json.load(f)
        
        expected_hash = metadata.get("target_hash")
        actual_hash = get_sha256(output_rom)
        
        if expected_hash == actual_hash:
            print("무결성 검증 성공! 패치가 정상적으로 적용되었습니다.")
        else:
            print("무결성 검증 실패! 결과 파일이 손상되었거나 원본 파일이 잘못되었을 수 있습니다.")
    else:
        print("경고: 메타데이터 파일이 없어 무결성 검증을 생략합니다.")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("사용법: python patcher.py <원본_ROM> <패치파일> <생성될_결과ROM>")
        sys.exit(1)
        
    apply_patch(sys.argv[1], sys.argv[2], sys.argv[3])
