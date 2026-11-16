"""Synthetic ZIP members exercise bounded original-byte/CRC validation."""
import copy,io,sys,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from acquire_davis_subset import decode

class DavisAcquisitionTests(unittest.TestCase):
    def fixture(self):
        f=io.BytesIO()
        with zipfile.ZipFile(f,'w',zipfile.ZIP_DEFLATED) as archive:archive.writestr('SYNTHETIC/a.txt',b'test payload')
        raw=f.getvalue()
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:info=archive.infolist()[0]
        return raw,info
    def test_exact_original_member_is_recovered_from_nonzero_range_offset(self):
        raw,info=self.fixture();self.assertEqual(decode(info,raw,0),b'test payload')
        shifted=copy.copy(info);shifted.header_offset+=1000
        self.assertEqual(decode(shifted,raw,1000),b'test payload')
    def test_crc_identity_size_and_truncation_mismatch_fail(self):
        raw,info=self.fixture()
        for key,value in [('CRC',info.CRC^1),('filename','wrong.txt'),('file_size',3*1024*1024)]:
            bad=copy.copy(info);setattr(bad,key,value)
            with self.assertRaises(ValueError):decode(bad,raw,0)
        with self.assertRaises(ValueError):decode(info,raw[:31],0)
