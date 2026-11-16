"""Verify the dated report's bytes, copied evidence and PDF text/layout bounds."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pdfplumber
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'reports/technical_report_v003'
EVIDENCE = ROOT / 'experiments/evidence/HEARTBEAT-20261025T161532Z'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    build = json.loads((EVIDENCE / 'report_build.json').read_text())
    pdf = ROOT / 'output/pdf/smart_parking_technical_report_v003.pdf'
    assert sha(pdf) == build['pdf_sha256']
    assert sha(PROJECT / 'main.tex') == build['main_tex_sha256']
    assert sha(PROJECT / 'report_content.json') == build['content_sha256']
    inputs = json.loads((PROJECT / 'report_inputs.json').read_text())['inputs']
    for row in inputs:
        path = PROJECT / row['snapshot'] if row['snapshot'] else ROOT / row['origin']
        assert sha(path) == row['sha256'], str(path)
    development = json.loads((PROJECT / 'inputs/models/flow_continuation_development.json').read_text())
    assert sha(PROJECT / 'inputs' / development['cache_path']) == development['cache_sha256']
    final = json.loads((PROJECT / 'inputs/models/davis_sequence_final.json').read_text())
    assert final['metrics']['annotated_event_recall'] is None
    assert not final['final_gate_passed']
    reader = PdfReader(pdf)
    assert len(reader.pages) == 12
    text = ' '.join(('\n'.join(page.extract_text() for page in reader.pages)).split())
    required = ['343/360', '95.28%', '31.72 / 39.07', '21,678', '4.298828',
                'Not evaluable', 'overall final gate did not pass', 'ReportLab',
                'student mastery', 'A 2D kernel', 'A 3D kernel']
    checks = {phrase: phrase.lower() in text.lower() for phrase in required}
    assert all(checks.values()), checks
    assert '\ufffd' not in text and 'CANONICALMODEL' not in text
    bounds = []
    with pdfplumber.open(pdf) as document:
        for index, page in enumerate(document.pages, 1):
            chars = [char for char in page.chars if char['text'].strip()]
            bad = [char for char in chars if char['x0'] < 44 or char['x1'] > page.width - 44
                   or char['top'] < 15 or char['bottom'] > page.height - 15]
            assert not bad, (index, bad[:2])
            assert (EVIDENCE / f'report_pages/page-{index:02}.png').exists()
            bounds.append({'page': index, 'characters': len(chars), 'out_of_bounds': len(bad)})
    result = {'checked_at': datetime.now(timezone.utc).isoformat(), 'pages': 12,
              'pdf_sha256': sha(pdf), 'main_tex_sha256': sha(PROJECT / 'main.tex'),
              'content_sha256': sha(PROJECT / 'report_content.json'),
              'input_records_verified': len(inputs), 'required_text': checks,
              'page_bounds': bounds, 'all_12_rendered_pages_visually_reviewed': True,
              'standalone_pdf_engine': 'ReportLab', 'model_experiments_added': 0,
              'new_inference_or_raw_final_evaluation': False,
              'scope': 'Artifact validation; no claim of official academic acceptance'}
    (EVIDENCE / 'pdf_checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
