import os

import struct

import json

import glob



def dynamic_repack_scd(original_scd_path, jsonl_path, output_path):

    """

    SCD ?뚯씪???ㅻ뜑 援ъ“(?ㅽ봽???뚯씠釉?瑜??꾩쟾??遺꾩꽍?섏뿬,

    ?띿뒪??湲몄씠媛� 蹂�?섎뜑?쇰룄 釉붾줉 ?ш린?� ?ъ씤?곕? ?먮룞?쇰줈 ?ш퀎?고빐 ?щ퉴?쒗빀?덈떎.

    """

    with open(original_scd_path, 'rb') as f:

        data = f.read()



    magic = data[:4]

    if magic != b'SCR\x00':

        print("Invalid magic number")

        return

        

    num_entries = struct.unpack('<I', data[4:8])[0]

    header_size = struct.unpack('<I', data[8:12])[0]

    

    # 1. 釉붾줉 ?뺣낫 ?뚯떛

    offset = 16

    blocks = []

    for i in range(num_entries):

        name_bytes = data[offset:offset+12]

        script_offset = struct.unpack('<I', data[offset+12:offset+16])[0]

        actual_offset = header_size + script_offset

        blocks.append({

            "index": i,

            "name_bytes": name_bytes,

            "original_actual_offset": actual_offset,

            "original_script_offset": script_offset,

            "data": bytearray()

        })

        offset += 16

        

    # 媛?釉붾줉???곗씠??異붿텧

    for i, block in enumerate(blocks):

        start_offset = block["original_actual_offset"]

        if i + 1 < len(blocks):

            end_offset = blocks[i+1]["original_actual_offset"]

        else:

            end_offset = len(data)

        block["data"] = bytearray(data[start_offset:end_offset])



    # 2. 蹂�寃쎌젏(Replacements) 以�鍮?    # 釉붾줉 ?몃뜳?ㅻ퀎濡?遺꾨쪟?⑸땲??

    replacements_by_block = {i: [] for i in range(num_entries)}

    

    try:

        with open('nftr_korean_mapping.json', 'r', encoding='utf-8') as mf:

            korean_mapping = json.load(mf)

    except:

        korean_mapping = {}



    target_jsonl = 'translated_texts.jsonl' if os.path.exists('translated_texts.jsonl') else jsonl_path



    with open(target_jsonl, 'r', encoding='utf-8') as f:

        for line in f:

            item = json.loads(line)

            # Remove .bak extension from original_scd_path for comparison

            base_name = os.path.basename(original_scd_path)

            if base_name.endswith('.bak'):

                base_name = base_name[:-4]

            if item["file"] == base_name:

                b_idx = item["block_index"]

                old_bytes = bytes.fromhex(item["raw_hex"])

                

                # ?띿뒪???몄퐫??濡쒖쭅 (?쒓? 留ㅽ븨 ?곸슜)

                if "translated_text" in item:

                    text_to_encode = item["translated_text"]

                    expected_len = len(old_bytes)
                    new_bytes_list = bytearray()
                    for c in text_to_encode:
                        if c in korean_mapping:
                            sjis_int = korean_mapping[c]['sjis']
                            char_bytes = [(sjis_int >> 8) & 0xFF, sjis_int & 0xFF]
                        else:
                            try:
                                char_bytes = list(c.encode('shift_jis'))
                            except:
                                char_bytes = [ord('?')]
                                
                        if len(new_bytes_list) + len(char_bytes) <= expected_len:
                            new_bytes_list.extend(char_bytes)
                        else:
                            break
                            
                    # Pad to exact expected_len with 0x00
                    diff = expected_len - len(new_bytes_list)
                    for _ in range(diff):
                        new_bytes_list.append(0x00)

                    new_bytes = bytes(new_bytes_list)

                else:

                    new_bytes = old_bytes

                

                # 釉붾줉 ???곷? ?ㅽ봽??怨꾩궛

                rel_offset = item["original_offset"] - blocks[b_idx]["original_actual_offset"]

                

                replacements_by_block[b_idx].append({

                    "rel_offset": rel_offset,

                    "old_bytes": old_bytes,

                    "new_bytes": new_bytes

                })



    # 3. 釉붾줉 ?곗씠???섏젙 (媛�蹂� 湲몄씠 吏�??

    for b_idx in range(num_entries):

        reps = replacements_by_block[b_idx]

        if not reps:

            continue

            

        # ?ㅼ뿉?쒕????섏젙?댁빞 ?곷? ?ㅽ봽?뗭씠 ??瑗ъ엫

        reps.sort(key=lambda x: x["rel_offset"], reverse=True)

        block_data = blocks[b_idx]["data"]

        

        for rep in reps:

            ro = rep["rel_offset"]

            old_b = rep["old_bytes"]

            new_b = rep["new_bytes"]

            

            # 臾닿껐??泥댄겕 (湲곗〈 ?곗씠?곗? ?꾩튂媛� 留욌뒗吏�)

            if block_data[ro:ro+len(old_b)] == old_b:

                # ?곗씠???щ씪?댁떛?쇰줈 湲몄씠 蹂�??援먯껜

                block_data = block_data[:ro] + new_b + block_data[ro+len(old_b):]

            else:

                print(f"Warning: Data mismatch in block {b_idx} at relative offset {ro}")

                

        blocks[b_idx]["data"] = block_data



    # 4. ?ㅻ뜑 諛????ㅽ봽???뚯씠釉?援ъ꽦

    new_file_data = bytearray()
    new_file_data.extend(data[:16])

    

    # 怨듯넻 ?ㅻ뜑 16諛붿씠??    new_file_data.extend(data[:16])

    

    # 5. 釉붾줉 ?곗씠?곕? ?⑹튂硫댁꽌 ???ㅽ봽??湲곕줉

    current_script_offset = 0

    header_entries_data = bytearray()

    blocks_data = bytearray()

    

    for block in blocks:

        # ?뷀듃由?異붽? (?대쫫 12諛붿씠??+ ???ㅽ봽??4諛붿씠??

        header_entries_data.extend(block["name_bytes"])

        header_entries_data.extend(struct.pack('<I', current_script_offset))

        

        # 釉붾줉 ?곗씠??蹂묓빀

        blocks_data.extend(block["data"])

        

        # ?ㅼ쓬 釉붾줉 ?ㅽ봽?뗭? ?꾩옱 釉붾줉 湲몄씠瑜??뷀븿

        current_script_offset += len(block["data"])

        

    new_file_data.extend(header_entries_data)

    new_file_data.extend(blocks_data)



    with open(output_path, 'wb') as f:

        f.write(new_file_data)

        

    print(f"Dynamic repacked file saved to {output_path}")



if __name__ == '__main__':

    for scd_file in glob.glob("data/*.scd"):

        if not scd_file.endswith('.bak'):

            bak_path = scd_file + ".bak"

            if not os.path.exists(bak_path):

                os.rename(scd_file, bak_path)

            

            if os.path.exists(bak_path):

                print(f"Repacking {scd_file}...")

                dynamic_repack_scd(bak_path, "translated_texts.jsonl", scd_file)



