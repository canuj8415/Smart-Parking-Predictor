"""Offline verification of already acquired official metadata, never image access."""
import argparse,collections,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.zip_metadata import inventory_tail,validate_range,decode_document_member,require_image_admission
RAW=ROOT/'data/raw/ndispark_official'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')


def prepare():
    now=datetime.now(timezone.utc);run_id='NDISPARK-METADATA-'+now.strftime('%Y%m%dT%H%M%S%fZ')
    out=ROOT/'experiments/results'/run_id;out.mkdir(parents=True,exist_ok=False)
    code=['scripts/qualify_ndispark_metadata.py','src/smart_parking/zip_metadata.py','tests/test_zip_metadata.py']
    p=dict(run_id=run_id,prepared_at=now.isoformat(),seed=144,source_ids=['SRC-DS-020','SRC-DOC-022'],
        hypothesis='Bounded metadata and exact README ranges can verify publisher inventory/document identity without admitting image content under a database-only licence.',
        data_kind='Official original metadata/document ranges;no image pixels or semantic annotation bodies',
        prior_exposure='Discovery, API, directory and README text already inspected before this integrity revalidation protocol;not a prospectively blind source discovery trial.',
        expected=dict(remote_archive_bytes=118187828,entries=271,jpegs=259,train=112,validation=30,test=117,readme_bytes=61306),
        gates=['Exact HTTP206range/length matches','Complete central-directory inventory','Local/central README name/size/CRC and bounded DEFLATE agree','Decoded README matches original saved copy','Database licence alone refuses image admission','Protected frozen files unchanged'],
        input_hashes={f.relative_to(ROOT).as_posix():digest(f) for f in RAW.iterdir() if f.is_file()},
        implementation_hashes={f:digest(ROOT/f) for f in code},protected_hashes=read(ROOT/'models/singapore_trend_development.json')['protected_hashes'],
        image_admission=False,individual_content_rights_qualified=False,role_manifest_sha256=None,
        boundaries='No whole archive download or MD5 verification. Initial tail includes39021opaque noncentral bytes retained undecoded. README document only decompressed;PDF embedded images unrendered. ODC-BY is a database licence,not sufficient individual-content evidence. No annotation/occupancy/model accuracy.')
    dump(out/'protocol.json',p);dump(out/'implementation_sources.json',{f:(ROOT/f).read_text(encoding='utf-8') for f in code});dump(out/'protocol_binding.json',dict(sha256=digest(out/'protocol.json')));print(str(out/'protocol.json'))


def run(path):
    path=Path(path).resolve();out=path.parent;p=read(path)
    assert out.is_relative_to((ROOT/'experiments/results').resolve()) and digest(path)==read(out/'protocol_binding.json')['sha256']
    assert not (out/'run.json').exists()
    start=datetime.now(timezone.utc);timer=time.monotonic()
    for f,h in {**p['input_hashes'],**p['implementation_hashes'],**p['protected_hashes']}.items():assert digest(ROOT/f)==h,f
    total=p['expected']['remote_archive_bytes'];probe=read(RAW/'range_probe_metadata.json');tail=(RAW/'archive_footer.bin').read_bytes()
    validate_range(probe['status'],probe['headers']['content-range'],total-len(tail),total-1,total,tail)
    inventory=inventory_tail(tail,total);directory=(RAW/'central_directory.bin').read_bytes();exact=inventory_tail(directory,total)
    assert inventory['entries']==exact['entries'] and inventory['total_entries']==271 and exact['tail_is_exclusively_metadata']
    assert inventory['noncentral_prefix_bytes']==39021
    original=read(RAW/'directory_inventory.json');assert original['entries']==inventory['entries']
    readme=next(e for e in inventory['entries'] if e['name']=='README.pdf')
    events=read(RAW/'readme_ranges.json')['events']
    for e in events:
        body=(ROOT/e['path']).read_bytes();assert digest(ROOT/e['path'])==e['sha256'];validate_range(206,e['headers']['Content-Range'],e['start'],e['end'],total,body)
    body=decode_document_member((RAW/'readme_local_header.bin').read_bytes(),(RAW/'readme_name_extra.bin').read_bytes(),(RAW/'readme_compressed.bin').read_bytes(),readme)
    assert body==(RAW/'README.pdf').read_bytes() and len(body)==61306
    api=read(next(RAW.glob('metadata_*.json')));assert api['metadata']['license']['id']=='odc-by'
    files=api['files'];assert len(files)==1 and files[0]['size']==total
    images=[e for e in inventory['entries'] if e['name'].lower().endswith('.jpg')];counts=collections.Counter(e['name'].split('/')[0] for e in images)
    assert len(images)==259 and dict(counts)==dict(train=112,validation=30,test=117)
    try:require_image_admission(p)
    except ValueError as error:rejection=str(error)
    else:raise AssertionError('Unqualified image content must remain blocked')
    checks=dict(exact_ranges=True,complete_directory=True,readme_crc_and_bytes=True,publisher_inventory=True,image_access_blocked=True,protected_hashes_unchanged=all(digest(ROOT/f)==h for f,h in p['protected_hashes'].items()))
    result=dict(run_id=p['run_id'],started_at=start.isoformat(),finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-timer,seed=p['seed'],protocol_sha256=digest(path),checks=checks,metadata_validation_passed=all(checks.values()),
        inventory=dict(entries=271,files=265,directories=6,jpegs=259,publisher_folder_counts=dict(counts),filename_prefixes=sorted({Path(e['name']).stem.split('_')[0] for e in images}),prefixes_verified_as_camera_ids=False,remote_archive_bytes=total,publisher_checksum=files[0]['checksum'],whole_archive_checksum_verified=False,initial_tail_bytes=len(tail),initial_noncentral_bytes_retained_undecoded=39021,exact_metadata_slice_bytes=len(directory),readme_network_bytes=sum(e['end']-e['start']+1 for e in events),readme_expanded_bytes=len(body)),
        database_license='odc-by',individual_content_rights_qualified=False,image_admission=False,access_rejection=rejection,image_members_completely_acquired=0,image_pixels_decoded=0,pdf_embedded_images_rendered=0,semantic_annotation_bodies_opened=0,model_calls=0,final_evaluation=False,production_promoted=False,
        publisher_readme_scope='TRAINdaytime/validation+testnight. TRAIN+validation haveCOCOinstances/dots,all vehicles mapped to car. TESTcountingCSVonly;no final instance-segmentation labels established.',
        limitations=p['boundaries'],prior_exposure=p['prior_exposure'])
    dump(out/'run.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run');args=parser.parse_args();run(args.run) if args.run else prepare()
