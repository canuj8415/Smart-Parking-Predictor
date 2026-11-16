import json,unittest
from unittest.mock import patch
from smart_parking.acpds_admission import development_only,validate_development

def split(name):return dict(file_names=[name],rois_list=[[[[0,0],[1,0],[1,1],[0,1]]]],occupancy_list=[[1]])
def body():return json.dumps(dict(test=dict(secret='SENTINEL } [ \\"'),valid=split('v.jpg'),train=split('t.jpg'))).encode()

class AdmissionTests(unittest.TestCase):
    def test_test_branch_never_deserialized(self):
        original=json.loads
        def guard(s,*a,**k):
            if 'SENTINEL' in s:raise AssertionError('Reserved semantic value decoded')
            return original(s,*a,**k)
        with patch('smart_parking.acpds_admission.json.loads',side_effect=guard):p=development_only(body())
        self.assertEqual(set(p),{'train','valid'})
        self.assertEqual(validate_development(p,{'images/t.jpg','images/v.jpg'})['train']['spaces'],1)
    def test_duplicate_and_unknown_partition_rejected(self):
        for b in [b'{"train":{},"valid":{},"test":{},"test":{}}',b'{"train":{},"valid":{},"test":{},"extra":{}}']:
            with self.assertRaises(ValueError):development_only(b)
    def test_truncation_mismatch_trailing_data_rejected(self):
        for b in [body()[:-1],body()+b'{}',body()[:-1]+b',}',b'{"train":{"x":[}},"valid":{},"test":{}}']:
            with self.assertRaises(ValueError):development_only(b)
    def test_cross_split_duplicate_rejected(self):
        with self.assertRaises(ValueError):validate_development(dict(train=split('a.jpg'),valid=split('a.jpg')),{'images/a.jpg'})
    def test_unsafe_names_and_nonfinite_rois_rejected(self):
        for name in ['../t.jpg','dir/t.jpg','dir\\t.jpg']:
            with self.assertRaises(ValueError):validate_development(dict(train=split(name),valid=split('v.jpg')),{'images/'+name,'images/v.jpg'})
        p=dict(train=split('t.jpg'),valid=split('v.jpg'));p['train']['rois_list'][0][0][0][0]=float('nan')
        with self.assertRaises(ValueError):validate_development(p,{'images/t.jpg','images/v.jpg'})
    def test_bad_labels_missing_files_and_degenerate_rois_rejected(self):
        p=dict(train=split('t.jpg'),valid=split('v.jpg'))
        with self.assertRaises(ValueError):validate_development(p,{'images/t.jpg'})
        p['train']['occupancy_list'][0][0]=2
        with self.assertRaises(ValueError):validate_development(p,{'images/t.jpg','images/v.jpg'})
    def test_explicit_publisher_booleans_preserved(self):
        p=dict(train=split('t.jpg'),valid=split('v.jpg'));p['train']['occupancy_list'][0][0]=True;p['valid']['occupancy_list'][0][0]=False
        r=validate_development(p,{'images/t.jpg','images/v.jpg'})
        self.assertEqual(r['train']['occupied_label1'],1);self.assertEqual(r['valid']['vacant_label0'],1)
        p['train']=split('t.jpg');p['train']['rois_list'][0][0]=[[0,0]]*4
        with self.assertRaises(ValueError):validate_development(p,{'images/t.jpg','images/v.jpg'})

if __name__=='__main__':unittest.main()
