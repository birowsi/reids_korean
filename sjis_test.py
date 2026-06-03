import sys

def test_sjis_force(hex_string):
    data = bytes.fromhex(hex_string)
    # SJIS 디코딩 후 터미널 출력 에러 방지를 위해 ascii로만 변환 가능한것만 출력, 한자는 유니코드값으로 출력
    try:
        text = data.decode('shift_jis', errors='ignore')
        safe_text = text.encode('ascii', errors='backslashreplace').decode('ascii')
        print(safe_text)
    except Exception as e:
        print("Error:", e)
        
    print("Raw decoded:")
    print(repr(data.decode('shift_jis', errors='ignore')))

if __name__ == '__main__':
    test_sjis_force("1c002800000020000e000d000b0026001a0015001b0028001100ae010a00310083418358834a817582a882a882c1814182e282e982b682e182c882a282a982a2814282a882dc82a682bd82bf81498176000b001100af010a00310088ea96a18260817583")
    print("---")
    test_sjis_force("1c002800000020000e000d000b0026001a001500160046001b0028001100d3010a00430088bb9467817582d382a482a3816381428da193fa82cc8ec08cb18376838d834f8389838082cd8f4997b982cb814282dd82c882b382f182a894e682ea82b382dc")
