"""Regression checks for a built patcher; does not modify project ROMs."""
import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

import validate_project
from repair_translation_review import REVIEW_FIXES, reviewed_translation, visible_count
from fix_crc import crc16

ROOT = Path(__file__).resolve().parent


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def encrypted_fixture(payload):
    padder = padding.PKCS7(128).padder()
    padded = padder.update(payload) + padder.finalize()
    iv = bytes(16)
    encryptor = Cipher(algorithms.AES(hashlib.sha256(b"0314").digest()), modes.CBC(iv)).encryptor()
    return iv + encryptor.update(padded) + encryptor.finalize()


class TranslationRegression(unittest.TestCase):
    def test_rank_particles(self):
        row = {"ID": "-1", "Japanese": "葛城三佐"}
        self.assertEqual(reviewed_translation(row, "삼좌가 소좌와 삼사는 삼좌를 삼사로"),
                         "소령이 소령과 소령은 소령을 소령으로")

    def test_duplicate_slash_is_not_a_valid_control(self):
        self.assertNotEqual(validate_project.LITERAL_CONTROL_PATTERN.findall(r"\1"),
                            validate_project.LITERAL_CONTROL_PATTERN.findall(r"\\1"))

    def test_csv_jsonl_drift_is_detected(self):
        original_loader = validate_project.load_jsonl

        def stale_loader(path):
            items = original_loader(path)
            if path.name == "translated_texts.jsonl":
                items[0]["translated_text"] += " "
            return items

        with patch.object(validate_project, "load_jsonl", stale_loader):
            errors, _, _ = validate_project.validate()
        self.assertTrue(any("stale relative to CSV" in error for error in errors))

    def test_reviewed_rows_are_character_safe(self):
        import csv
        with (ROOT / "translation_work.csv").open(encoding="utf-8", newline="") as source:
            rows = list(csv.DictReader(source))
        for row in rows:
            if row["ID"] in REVIEW_FIXES:
                self.assertEqual(row["Korean"], REVIEW_FIXES[row["ID"]])
                self.assertLessEqual(visible_count(row["Korean"]), visible_count(row["Japanese"]))


class BuiltRomRegression(unittest.TestCase):
    def test_header_assets_and_packed_scripts(self):
        with (ROOT / "rei.nds").open("rb") as rom:
            header = rom.read(0x200)
            self.assertEqual(struct.unpack_from("<H", header, 0x15C)[0], crc16(header[0xC0:0x15C]))
            self.assertEqual(struct.unpack_from("<H", header, 0x15E)[0], crc16(header[:0x15E]))
            self.assertEqual(header[0x6C:0x6E], (ROOT / "header.bin").read_bytes()[0x6C:0x6E])
            arm9_offset, _, _, arm9_size = struct.unpack_from("<IIII", header, 0x20)
            rom.seek(arm9_offset)
            arm9_source = (ROOT / "arm9.bin").read_bytes()
            # ndstool excludes the Nitro 12-byte module footer from header size,
            # but retains those bytes immediately after the executable region.
            self.assertEqual(arm9_source[arm9_size:arm9_size + 4], b"\x21\x06\xc0\xde")
            self.assertEqual(len(arm9_source), arm9_size + 12)
            self.assertEqual(hashlib.sha256(rom.read(len(arm9_source))).digest(),
                             hashlib.sha256(arm9_source).digest())
            fnt_offset, fnt_size, fat_offset, fat_size = struct.unpack_from("<IIII", header, 0x40)
            rom.seek(fnt_offset)
            fnt = rom.read(fnt_size)
            rom.seek(fat_offset)
            fat = rom.read(fat_size)
            files = {}

            def directory(directory_id, prefix=""):
                offset, file_id, _ = struct.unpack_from("<IHH", fnt, (directory_id & 0xFFF) * 8)
                while fnt[offset]:
                    tag = fnt[offset]
                    offset += 1
                    name = fnt[offset:offset + (tag & 0x7F)].decode("ascii")
                    offset += tag & 0x7F
                    if tag & 0x80:
                        child = struct.unpack_from("<H", fnt, offset)[0]
                        offset += 2
                        directory(child, prefix + name + "/")
                    else:
                        files[prefix + name] = file_id
                        file_id += 1

            directory(0xF000)
            self.assertFalse(any(name.endswith(".bak") for name in files))
            for name in ("aya.scd", "asuka.scd", "title.scd"):
                start, end = struct.unpack_from("<II", fat, files[name] * 8)
                rom.seek(start)
                self.assertEqual(rom.read(end - start), (ROOT / "data" / name).read_bytes())


class PatcherRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_hash = digest(ROOT / "original.nds")
        cls.target_hash = json.loads((ROOT / "korean_patch_v6.xdelta.meta").read_text())["target_hash"]

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="reids-patcher-test-")
        self.base = Path(self.temp.name)
        self.patcher = self.base / "패처 폴더"
        self.patcher.mkdir()
        self.other = self.base / "different-cwd"
        self.other.mkdir()
        for name in ("Korean_Patcher.exe", "korean_patch_v6.dat", "xdelta3.exe"):
            shutil.copy2(ROOT / name, self.patcher / name)
        self.output = self.patcher / "rei.nds"

    def tearDown(self):
        self.temp.cleanup()

    def run_patcher(self, original=None, pin="0314", cwd=None):
        return subprocess.run(
            [str(self.patcher / "Korean_Patcher.exe"), str(original or ROOT / "original.nds")],
            input=(pin + "\n\n").encode("utf-8"), stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, cwd=cwd or self.other, timeout=60,
        )

    def assert_failure_preserves_output(self, **kwargs):
        sentinel = b"existing output must survive"
        self.output.write_bytes(sentinel)
        result = self.run_patcher(**kwargs)
        self.assertNotEqual(result.returncode, 0, result.stdout.decode("utf-8", errors="replace"))
        self.assertEqual(self.output.read_bytes(), sentinel)
        self.assertEqual(list(self.patcher.glob("rei.nds.*.tmp")), [])

    def test_success_from_other_cwd_and_atomic_replace(self):
        for preexisting in (False, True):
            if preexisting:
                self.output.write_bytes(b"previous output")
            result = self.run_patcher()
            self.assertEqual(result.returncode, 0, result.stdout.decode("utf-8", errors="replace"))
            self.assertEqual(digest(self.output), self.target_hash)
        self.assertEqual(digest(ROOT / "original.nds"), self.original_hash)

    def test_input_equals_output_is_rejected(self):
        self.assert_failure_preserves_output(original=self.output)

    def test_wrong_rom(self):
        wrong = self.base / "wrong.nds"
        wrong.write_bytes(b"not the supported ROM")
        self.assert_failure_preserves_output(original=wrong)

    def test_wrong_pin(self):
        self.assert_failure_preserves_output(pin="incorrect")

    def test_empty_pin(self):
        self.assert_failure_preserves_output(pin="")

    def test_corrupt_dat(self):
        (self.patcher / "korean_patch_v6.dat").write_bytes(bytes(17))
        self.assert_failure_preserves_output()

    def test_decoder_failure(self):
        (self.patcher / "korean_patch_v6.dat").write_bytes(encrypted_fixture(b"not an xdelta patch"))
        self.assert_failure_preserves_output()

    def test_target_hash_failure(self):
        target = self.base / "wrong-target.bin"
        delta = self.base / "wrong-target.xdelta"
        target.write_bytes(b"valid delta but wrong target hash")
        subprocess.run([str(ROOT / "xdelta3.exe"), "-e", "-s", str(ROOT / "original.nds"),
                        str(target), str(delta)], check=True, capture_output=True, timeout=60)
        (self.patcher / "korean_patch_v6.dat").write_bytes(encrypted_fixture(delta.read_bytes()))
        self.assert_failure_preserves_output()


if __name__ == "__main__":
    unittest.main(verbosity=2)
