# Count vehicles crossing an entrance line

Think of a shop doorway: one person crossing in one direction means entering;
crossing back means leaving. The program applies that idea to vehicle boxes in
a video. It does not know which side is your entrance until you tell it.

1. Start the Python app with `launch_parking.cmd` and open **Entrance / exit**.
2. Choose **Open local video** and select a video you are allowed to use. The
   first frame appears. This feature opens a file, not a webcam or online stream.
3. Choose **Draw counting line**. Click two different points across the actual
   entrance. Click inside the picture, not its surrounding margin.
4. The cyan line is the counting boundary. The orange arrow shows a reference
   direction across it. Explicitly select **Along orange arrow** or **Against
   orange arrow** to say which movement means entering. Leaving is the opposite.
5. Use **Save setup** to retain that line and direction. **Load setup** accepts
   the same video bytes and first-frame pixels; matching picture dimensions alone
   are insufficient. Re-encoded or edited videos need a fresh setup. Setups with
   advanced tracker settings are reserved for the existing command-line tool.
6. Choose a maximum of 1–240 sampled frames, then **Run count**. The default is
   30 frames, sampled at half-second video intervals, covering about 14.5 seconds
   for a regular video. Processing on this laptop can be slower than playback.
7. **Stop video** cancels processing. Cancelling before the first processed frame
   produces no prediction. Cancelling later retains the partial results and marks
   them as cancelled.

Results are saved automatically in a new folder below `outputs/flow/`:

| File | What it contains |
|---|---|
| `source_and_gate.json` | Exact local video path/checksum, first-frame checksum, line, direction, detector identity, processing limit and completion/failure status |
| `observations.csv` | Video timestamps, detected vehicle count and predicted entering/leaving totals for each processed frame |
| `detections.jsonl` | Per-frame vehicle boxes, tracking decisions and predicted crossing events |
| `events.json` | Summary, predicted counts and cancellation state |
| `frame_*.jpg` | Processed pictures with detection boxes, counting line and track identifiers |

A failure preserves the setup and error record; a completed summary is not
invented. Before the first frame there may be no observation table or images.
Existing results folders are never reused by this feature.

Counts are predictions. Occlusion, missed detections and ambiguous vehicle
associations can lose crossings. A long observation gap resets tracking evidence.
The line must match the actual entrance and camera view. Crossing a line on an
ordinary street is not automatically a parking entry. This tab does not infer
parking-space occupancy or predict availability from the count.

The development check reused **Street traffic**, by Editor, via Wikimedia
Commons, [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/), source
`SRC-VID-001`. Its original video is retained at
`data/raw/wikimedia_street_traffic/Street_traffic.webm`; the exact source URL,
creator, licence and receipt are in `data/source_manifest.csv` and
`data/resource_receipts.jsonl`. The three-frame integration trial is
`experiments/results/DESKTOP-FLOW-20261025T091303623986Z/`. It produced zero
predicted crossings in this short segment. There are no independently labelled
crossings here, so real-world counting accuracy remains unmeasured.

The hidden native-widget check tested the app's controls and actual setup-file
save/reload methods, with file dialogs replaced by test selections. It does not
establish physical dialog interaction, visual layout approval or a human rehearsal.
