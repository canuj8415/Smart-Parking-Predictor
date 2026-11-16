"""Fingerprints of the actual pixels and inference geometry, not camera identity."""
import hashlib,json

def image_identity(image):
    rgb=image if image.mode=='RGB' else image.convert('RGB')
    digest=hashlib.sha256(f'RGB:{rgb.width}x{rgb.height}\0'.encode('ascii'))
    digest.update(rgb.tobytes())
    return dict(sha256=digest.hexdigest(),width=rgb.width,height=rgb.height,
        encoding='SHA256 of ASCII RGB:WIDTHxHEIGHT followed by NUL and row-major RGB bytes; identifies processed pixels, not original file metadata')

def layout_identity(layout):
    if layout is None:return None
    geometry=dict(camera_id=layout['camera_id'],image_size=layout['image_size'],
        slots=[dict(id=s['id'],polygon=s['polygon']) for s in layout['slots']])
    raw=json.dumps(geometry,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')
    return dict(sha256=hashlib.sha256(raw).hexdigest(),camera_id=layout['camera_id'],spaces=len(layout['slots']),
        encoding='Canonical UTF8 JSON of camera_id/image_size/ordered slot IDs and polygons; excludes ground-truth occupancy and descriptive metadata',
        limitation='Geometry fingerprint does not authenticate camera identity or prove view alignment')
