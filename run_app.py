"""Launch the complete local Python desktop application."""
import argparse,json,os,sys,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'src'))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
from smart_parking.environment import environment_report,setup_message


def launch():
    parser=argparse.ArgumentParser(description='Smart Parking local desktop product')
    parser.add_argument('--check-environment',action='store_true',help='Report local prerequisites without opening the app or loading models')
    args=parser.parse_args();report=environment_report(ROOT)
    if args.check_environment:
        print(json.dumps(report,indent=2));return 0 if report['prerequisites_found'] else 2
    if report['missing_required']:
        print(setup_message(report),file=sys.stderr);return 2
    try:from smart_parking.app import main
    except (ImportError,OSError,RuntimeError):
        path=ROOT/'.cache/startup_error.log'
        try:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(traceback.format_exc(),encoding='utf-8')
        except OSError:pass
        print('Smart Parking could not load an installed component. Use a compatible app environment.\n'
              'See docs/INSTALLATION_READINESS.md; technical details are in .cache/startup_error.log.\n'
              'No models were loaded and nothing was installed.',file=sys.stderr)
        return 3
    main();return 0


if __name__=='__main__':raise SystemExit(launch())
