# Lesson 4: counting at an imaginary gate

Imagine a guard at a driveway. The guard remembers a car, waits until it is
clearly on one side of a painted line, then records an entry when it appears
clearly on the other side. Our new Python counter follows that idea using the
centre of the detector's vehicle box. It saves an identity number, direction,
video time and cumulative counts.

The event time is when the new side is confirmed by the required observations;
it is later than the physical line crossing. It is not an exact crossing-time
measurement.

The directed line has two endpoints. Its left side is called positive. For the
horizontal example pointing right, below the line is positive. The supplied
street example calls above-to-below an entry. This is an illustration on a road,
not an actual parking entrance or proof of correct real-world counts.

The counter needs two stable observations on each side and ignores a six-pixel
band around the line. It suppresses heavily overlapping vehicle boxes, drops
ambiguous identities, rejects invalid coordinates/timestamps and resets when the
gap exceeds 0.75 seconds. These choices reduce unsupported counts but can miss
vehicles. They do not solve occlusion or identity tracking. Two-second samples
are too far apart for this configuration; zero counts after resets mean the
counter abstained, not that no vehicles crossed.

Gate crossings and parking occupancy answer different questions. A crossing says
that a predicted vehicle moved through a configured gate. Occupancy says that a
particular parking space is occupied. The road example has no parking layout,
so it produces no occupied/free-space counts. Singapore's aggregate live feed
provides neither camera tracks nor correct gate counts.

The integration is available through `process_video(..., flow_config=...)` and
the local-file command below. The current desktop video button continues its
existing occupancy workflow; a graphical gate editor remains unfinished.

From the project directory, using the project Python environment:

```powershell
& 'D:/deep learning/.venv/Scripts/python.exe' scripts/process_gate_video.py --source data/raw/wikimedia_street_traffic/Street_traffic.webm --gate-config configs/street_gate_demo.json --attribution data/raw/wikimedia_street_traffic/acquisition.json --output output/my_gate_demo --interval 0.5 --max-frames 25
```

Choose a new output directory to preserve earlier results. Press Ctrl+C to stop;
the validation helper also supports an empty `CANCEL` file in its run directory.
The generic command watches its output directory for that file. Completed frames
are flushed to `detections.jsonl`; a cancelled partial sequence is not a complete
accuracy benchmark.

Outputs include annotated frame images with a cyan gate/identity labels,
`observations.csv` with predicted entries/exits and timing,
`detections.jsonl` with original detector predictions plus flow records, and
`events.json` with settings, crossings and diagnostic resets. The generic command
also saves source checksums and supplied attribution in `source_and_gate.json`.

For your own authorized video, define the actual frame dimensions and driveway
line, state which direction means entry, and record its creator/permission.
Matching dimensions alone cannot prove that the camera is the right one.
Before claiming accuracy, reserve a separate labelled video, manually mark true
crossing times/directions and identities, then compare a frozen configuration
against those answers. The present real-video exercise checks operation and
export consistency only.

Source: *Street traffic*, Editor, via Wikimedia Commons, CC BY 3.0. Original URL:
https://commons.wikimedia.org/wiki/File:Street_traffic.webm . Derived overlays
add model predictions, a gate and identity numbers. No endorsement is implied.
