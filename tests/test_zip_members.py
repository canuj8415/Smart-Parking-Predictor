import struct,unittest,zlib
from smart_parking.zip_members import image_member_span,decode_jpeg_member,validate_member_range

def fixture():
    image=b'\xff\xd8fixture\xff\xd9';c=zlib.compressobj(wbits=-15);compressed=c.compress(image)+c.flush();name=b'images/train.JPG';crc=zlib.crc32(image)
    header=struct.pack('<4s5H3I2H',b'PK\x03\x04',20,8,8,0,0,0,0,len(image),len(name),0)
    body=header+name+compressed+struct.pack('<4s3I',b'PK\x07\x08',crc,len(compressed),len(image))
    e=dict(name=name.decode(),size=len(image),compressed_size=len(compressed),method=8,crc32=crc,header_offset=0,directory=False)
    return image,body,e

class ZipMemberTests(unittest.TestCase):
    def test_unadmitted_and_traversal_blocked_before_range(self):
        _,b,e=fixture();inv=dict(entries=[e],central_offset=len(b),total_bytes=len(b)+22)
        with self.assertRaisesRegex(ValueError,'not admitted'):image_member_span('images/final.JPG',{e['name']},inv)
        with self.assertRaisesRegex(ValueError,'Unsafe'):image_member_span('images/../train.JPG',{'images/../train.JPG'},inv)
        self.assertEqual(image_member_span(e['name'],{e['name']},inv)[1:],(0,len(b)-1))
    def test_crc_descriptor_and_trailing_bytes(self):
        image,b,e=fixture();self.assertEqual(decode_jpeg_member(b,e),image)
        for bad in [b[:-1],b+b'X',b[:-15]+bytes([b[-15]^1])+b[-14:]]:
            with self.assertRaises(ValueError):decode_jpeg_member(bad,e)
        wrong=dict(e,crc32=e['crc32']^1)
        with self.assertRaises(ValueError):decode_jpeg_member(b,wrong)
    def test_name_encryption_method_and_bomb_rejected(self):
        _,b,e=fixture()
        for wrong in [dict(e,name='images/other.JPG'),dict(e,size=9_000_000),dict(e,method=0)]:
            with self.assertRaises(ValueError):decode_jpeg_member(b,wrong)
        bad=bytearray(b);struct.pack_into('<H',bad,6,9)
        with self.assertRaises(ValueError):decode_jpeg_member(bytes(bad),e)
    def test_exact_range_and_etag_required(self):
        validate_member_range(206,'bytes 3-5/10',3,5,10,b'abc','"a"','"a"')
        for status,cr,b,etag in [(200,'bytes 3-5/10',b'abc','"a"'),(206,'bytes 0-2/10',b'abc','"a"'),(206,'bytes 3-5/10',b'ab','"a"'),(206,'bytes 3-5/10',b'abc','"changed"')]:
            with self.assertRaises(ValueError):validate_member_range(status,cr,3,5,10,b,etag,'"a"')
    def test_duplicate_members_and_oversize_span_rejected(self):
        _,b,e=fixture()
        with self.assertRaises(ValueError):image_member_span(e['name'],{e['name']},dict(entries=[e,e],central_offset=len(b),total_bytes=len(b)+22))
        with self.assertRaises(ValueError):image_member_span(e['name'],{e['name']},dict(entries=[e],central_offset=9_000_000,total_bytes=9_000_022))

if __name__=='__main__':unittest.main()
