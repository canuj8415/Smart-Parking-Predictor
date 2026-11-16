import io
import struct
import unittest
import zipfile
from smart_parking.zip_metadata import inventory_tail,validate_range,require_document_member,require_image_admission,decode_document_member


def fixture(comment=b''):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as z:
        z.writestr('README.pdf',b'synthetic document');z.writestr('train/image.jpg',b'synthetic fixture,not image pixels');z.comment=comment
    return stream.getvalue()


class ZipMetadataTests(unittest.TestCase):
    def test_inventory_reports_overfetch_honestly(self):
        data=fixture();result=inventory_tail(data,len(data))
        self.assertEqual(result['total_entries'],2);self.assertGreater(result['noncentral_prefix_bytes'],0)
        self.assertFalse(result['tail_is_exclusively_metadata']);self.assertFalse(result['whole_archive_integrity_verified'])

    def test_exact_directory_has_no_member_body(self):
        data=fixture();result=inventory_tail(data,len(data));offset=result['central_offset'];exact=inventory_tail(data[offset:],len(data))
        self.assertTrue(exact['tail_is_exclusively_metadata']);self.assertEqual(exact['entries'][0]['header_offset'],0)

    def test_signature_in_comment_does_not_hide_real_end_record(self):
        data=fixture(b'comment PK\x05\x06');self.assertEqual(inventory_tail(data,len(data))['total_entries'],2)

    def test_truncated_or_multidisk_metadata_rejected(self):
        data=fixture()
        with self.assertRaises(ValueError):inventory_tail(data[:-1],len(data))
        altered=bytearray(data);position=data.rfind(b'PK\x05\x06');struct.pack_into('<H',altered,position+4,1)
        with self.assertRaises(ValueError):inventory_tail(bytes(altered),len(altered))

    def test_range_requires_exact206_size_total_and_budget(self):
        validate_range(206,'bytes 2-4/10',2,4,10,b'abc')
        for status,header,body in [(200,'bytes 2-4/10',b'abc'),(206,'bytes 2-4/11',b'abc'),(206,'bytes 2-4/10',b'abcd')]:
            with self.assertRaises(ValueError):validate_range(status,header,2,4,10,body)

    def test_readme_whitelist_never_opens_images_or_labels(self):
        require_document_member('README.pdf')
        for name in ['../README.pdf','train/README.pdf','train/train_coco_annotations.json','test/ground_truth_test_counting.csv','train/image.jpg']:
            with self.assertRaises(ValueError):require_document_member(name)

    def test_database_license_does_not_automatically_admit_content(self):
        for license_id in ['odc-by','odbl-1.0','cc-by-4.0']:
            with self.assertRaises(ValueError):require_image_admission(dict(database_license_id=license_id))
        with self.assertRaises(ValueError):require_image_admission(dict(individual_content_rights_qualified=True))

    def test_readme_expansion_checks_crc_and_size(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as archive:archive.writestr('README.pdf',b'synthetic document')
        data=stream.getvalue();entry=inventory_tail(data,len(data))['entries'][0];head=data[:30];fields=struct.unpack('<4s5H3I2H',head);names=data[30:30+fields[-2]+fields[-1]];body=data[30+len(names):30+len(names)+entry['compressed_size']]
        self.assertEqual(decode_document_member(head,names,body,entry),b'synthetic document')
        corrupt=dict(entry,crc32=0)
        with self.assertRaises(ValueError):decode_document_member(head,names,body,corrupt)
        with self.assertRaises(ValueError):decode_document_member(head,names,body[:-1],entry)

    def test_local_name_and_expansion_budget_cannot_bypass_whitelist(self):
        import zlib
        value=b'A'*140000;compressor=zlib.compressobj(wbits=-15);payload=compressor.compress(value)+compressor.flush();crc=zlib.crc32(value)
        head=struct.pack('<4s5H3I2H',b'PK\x03\x04',20,0,8,0,0,crc,len(payload),len(value),10,0)
        entry=dict(name='README.pdf',compressed_size=len(payload),size=len(value),crc32=crc,method=8)
        with self.assertRaises(ValueError):decode_document_member(head,b'README.pdf',payload,entry)
        with self.assertRaises(ValueError):decode_document_member(head,b'image0.jpg',payload,entry)
