"""Dependency discovery before heavy imports; never installs or downloads packages."""
import importlib.metadata
import importlib.util
import platform
import sys
from pathlib import Path

COMPONENTS=[('torch','torch','vehicle models'),('torchvision','torchvision','image models'),
            ('numpy','numpy','image arithmetic'),('PIL','Pillow','image files'),
            ('matplotlib','matplotlib','charts'),('tkinter',None,'desktop window')]


def environment_report(root):
    root=Path(root);components=[]
    for module,distribution,purpose in COMPONENTS:
        try:found=importlib.util.find_spec(module) is not None
        except (ImportError,ValueError,AttributeError):found=False
        version=None
        if distribution:
            try:version=importlib.metadata.version(distribution)
            except importlib.metadata.PackageNotFoundError:pass
        components.append(dict(module=module,distribution=distribution,purpose=purpose,
                               found=found,version=version))
    local_decoder=root/'dependencies/python/cv2/__init__.py'
    try:global_decoder=importlib.util.find_spec('cv2') is not None
    except (ImportError,ValueError,AttributeError):global_decoder=False
    missing=[row['module'] for row in components if not row['found']]
    return dict(python_executable=sys.executable,python_version=platform.python_version(),
                tested_python_series='3.12',tested_python_series_matches=sys.version_info[:2]==(3,12),
                components=components,missing_required=missing,prerequisites_found=not missing,
                video_decoder_discovered=local_decoder.is_file() or global_decoder,
                discovery_only=True,binary_compatibility_tested=False,model_files_checked=False,
                gui_started=False,packages_installed=False,network_used=False,
                scope='Module discovery only; successful model loading and full offline installation require separate validation')


def setup_message(report):
    labels={row['module']:row['purpose'] for row in report['components']}
    names=', '.join(labels[name] for name in report['missing_required'])
    return ('Smart Parking cannot start with this Python installation.\n'
            'Missing components: '+names+'.\n'
            'Use the configured project Python, or prepare the complete app environment.\n'
            'See docs/INSTALLATION_READINESS.md. Nothing was downloaded or installed.')
