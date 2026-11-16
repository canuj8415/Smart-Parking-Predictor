"""Synthetic feed mutations; fixtures are not real parking observations."""
import copy
import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.live import parse_feed
from smart_parking import live


def fixture():
    return {'items':[{'timestamp':'2026-10-25T16:00:00+00:00','carpark_data':[
        {'carpark_number':'FIXTURE','update_datetime':'2026-10-26T00:00:00',
         'carpark_info':[{'total_lots':'10','lots_available':'3','lot_type':'C'}]}]}]}


class LiveQualityTests(unittest.TestCase):
    def test_identical_observations_collapse_across_equivalent_timezones(self):
        payload=fixture();park=copy.deepcopy(payload['items'][0]['carpark_data'][0])
        park['update_datetime']='2026-10-25T16:00:00+00:00'
        payload['items'][0]['carpark_data'].append(park)
        self.assertEqual(len(parse_feed(payload)),1)

    def test_conflicting_duplicate_is_not_selected_by_input_order(self):
        payload=fixture();parks=payload['items'][0]['carpark_data']
        other=copy.deepcopy(parks[0]);other['carpark_info'][0]['lots_available']='4';parks.append(other)
        for records in [parks,list(reversed(parks))]:
            payload['items'][0]['carpark_data']=records
            with self.assertRaisesRegex(ValueError,'Conflicting duplicate'):parse_feed(payload)

    def test_different_lot_types_remain_separate(self):
        payload=fixture();info=payload['items'][0]['carpark_data'][0]['carpark_info']
        other=copy.deepcopy(info[0]);other['lot_type']='M';info.append(other)
        self.assertEqual(len(parse_feed(payload)),2)

    def test_empty_identifiers_are_rejected(self):
        for key in ['carpark_number','lot_type']:
            for bad in ['', '   ', None, 3]:
                with self.subTest(key=key,bad=bad):
                    payload=fixture();park=payload['items'][0]['carpark_data'][0]
                    (park if key=='carpark_number' else park['carpark_info'][0])[key]=bad
                    with self.assertRaises(ValueError):parse_feed(payload)

    def test_noninteger_counts_never_truncate_or_accept_boolean(self):
        for key in ['total_lots','lots_available']:
            for bad in [True,False,3.9,3.0,'3.9',None]:
                with self.subTest(key=key,bad=bad):
                    payload=fixture();payload['items'][0]['carpark_data'][0]['carpark_info'][0][key]=bad
                    with self.assertRaises(ValueError):parse_feed(payload)

    def test_impossible_capacity_rows_still_excluded(self):
        payload=fixture();info=payload['items'][0]['carpark_data'][0]['carpark_info']
        for total,available in [('0','0'),('2','3'),('10','-1')]:
            other=copy.deepcopy(info[0]);other.update(total_lots=total,lots_available=available);info.append(other)
        rows=parse_feed(payload);self.assertEqual(len(rows),1);self.assertEqual(rows[0]['occupied'],7)

    def test_new_observation_time_is_not_a_duplicate(self):
        payload=fixture();park=copy.deepcopy(payload['items'][0]['carpark_data'][0])
        park['update_datetime']='2026-10-26T00:00:01';park['carpark_info'][0]['lots_available']='4'
        payload['items'][0]['carpark_data'].append(park)
        self.assertEqual(len(parse_feed(payload)),2)

    def test_refresh_keeps_both_raw_receipts_but_one_semantic_history_row(self):
        parent=Path(__file__).resolve().parents[1]/'.cache/test_tmp';parent.mkdir(parents=True,exist_ok=True)
        first=fixture();second=copy.deepcopy(first)
        second['items'][0]['carpark_data'][0]['update_datetime']='2026-10-25T16:00:00+00:00'
        with tempfile.TemporaryDirectory(dir=parent) as temporary:
            root=Path(temporary)
            responses=[io.BytesIO(json.dumps(payload).encode()) for payload in [first,second]]
            with patch.object(live,'ROOT',root), patch.object(live,'latest_snapshot',side_effect=FileNotFoundError), \
                 patch.object(live,'receipt') as receipts, patch.object(live.urllib.request,'urlopen',side_effect=responses):
                live.get_live(refresh=True);live.get_live(refresh=True)
            self.assertEqual(receipts.call_count,2)
            self.assertEqual(len(list((root/'data/raw/singapore_live').glob('*.json'))),2)
            with (root/'data/processed/singapore_live_observations.csv').open(newline='') as stream:
                rows=list(csv.DictReader(stream))
            self.assertEqual(len(rows),1);self.assertEqual(rows[0]['observed_at'],'2026-10-26T00:00:00')

    def test_rejected_bytes_retained_without_replacing_usable_cache_or_history(self):
        conflicting=fixture();parks=conflicting['items'][0]['carpark_data']
        other=copy.deepcopy(parks[0]);other['carpark_info'][0]['lots_available']='4';parks.append(other)
        for raw in [b'{"items":',b'[]',b'null',json.dumps(conflicting).encode()]:
            with self.subTest(raw=raw[:20]):
                parent=Path(__file__).resolve().parents[1]/'.cache/test_tmp';parent.mkdir(parents=True,exist_ok=True)
                with tempfile.TemporaryDirectory(dir=parent) as temporary:
                    root=Path(temporary);accepted=root/'data/raw/singapore_live';accepted.mkdir(parents=True)
                    good=accepted/'20261025T000000Z.json';good.write_bytes(json.dumps(fixture()).encode())
                    with patch.object(live,'ROOT',root), patch.object(live,'receipt') as receipts:
                        with patch.object(live,'latest_snapshot',side_effect=FileNotFoundError), \
                             patch.object(live.urllib.request,'urlopen',return_value=io.BytesIO(raw)):
                            with self.assertRaisesRegex(ValueError,'rejected bytes saved separately'):live.get_live(refresh=True)
                        self.assertEqual(live.latest_snapshot(),good)
                    rejected=list((root/'data/raw/singapore_live_rejected').glob('*.json'))
                    self.assertEqual(len(rejected),1);self.assertEqual(rejected[0].read_bytes(),raw)
                    self.assertEqual(receipts.call_count,1)
                    self.assertFalse((root/'data/processed/singapore_live_observations.csv').exists())


if __name__=='__main__':unittest.main()
