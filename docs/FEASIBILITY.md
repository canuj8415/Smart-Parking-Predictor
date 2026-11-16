# Hardware and technical feasibility — provisional

**Active stack update:** Python 3.12.10 and JupyterLab 4.6.3 are available in the existing `D:\deep learning\.venv` environment. The user explicitly selected Python/Jupyter. The C++/Java comparison below is historical and superseded. Existing PyTorch is 2.14.0+cpu; an actual import reported CUDA unavailable. No packages were installed. See PYTHON_WORKFLOW.md.

Measured locally on 24 October 2026. Hardware capability is not a benchmark.

## Observed computer

| Item | Evidence |
|---|---|
| OS | Windows 11 Home Single Language, 64-bit, build 26200 |
| CPU | Intel Core i9-14900HX, 24 cores, 32 logical processors |
| Physical RAM | 16,869,548,032 bytes, approximately 15.71 GiB |
| Available OS memory at query | Approximately 3.72 GiB; changes with running applications |
| GPU | NVIDIA GeForce RTX 4070 Laptop GPU |
| GPU memory | 8,188 MiB reported by nvidia-smi |
| GPU driver | 610.62 |
| C: free space | Approximately 15.24 GiB |
| D: free space | Approximately 20.40 GiB; workspace is on D: |
| E: free space | Approximately 103.26 GiB; observed only, not selected for storage |
| Java | Temurin JDK/javac 25.0.3 installed |
| Git | Installed; workspace was not a repository |
| C++ tools | cl, g++, clang++ and cmake not found on PATH or checked common locations |
| Visual Studio discovery | Only SQL Server Management Studio returned; no verified C++ build tools |
| Maven | Not found on PATH |

The initial CIM hardware read was restricted. A subsequent authorized read-only
CIM query succeeded. GPU details came from nvidia-smi. Disk space came from
PowerShell filesystem drives. No CUDA toolkit, LibTorch, OpenCV, DJL engine or
working GPU training environment has been verified.

## Candidate comparison

| Criterion | C++ with LibTorch | Java with DJL |
|---|---|---|
| Current setup | Compiler and CMake unverified/missing | JDK present; build manager unverified |
| Native training | Direct C++ frontend supports training | PyTorch engine supports training through Java API |
| Vision integration | OpenCV has a native C++ interface | Requires appropriate Java/native integration |
| Baseline transparency | Standard-library MLP exposes all computations | Standard-library MLP is equally possible |
| Installation risks | Compiler, DLL and build-configuration compatibility | JNI/engine versions, caches and native DLL compatibility |
| Offline packaging | Cache headers, libraries, tools, runtime DLLs and weights | Cache build artifacts, engine native libraries and weights |
| Present proof | No compile/train test performed | javac availability only; no DJL training test performed |

**Historical candidate, now superseded:** C++17, LibTorch, OpenCV and CMake, with a
standard-library baseline and CPU fallback. This follows the user's preference
and offers a coherent route for native training and vision. Java's existing JDK
is a practical advantage, but it does not remove the native engine dependencies.
The final decision waits for the document audit and a minimal build/training
test; no libraries or versions have been selected or installed.

LibTorch provides C++ tensors, automatic differentiation, modules, optimizers,
data loading and checkpoint facilities. Windows Debug/Release libraries must
match the build configuration. [Frontend](https://docs.pytorch.org/cppdocs/frontend.html),
[installation](https://docs.pytorch.org/cppdocs/installing.html).

DJL's PyTorch engine supports Windows CPU/GPU packages and may download native
libraries on first use. Offline packaging must provide these ahead of time.
Verify JDK and engine compatibility in a smoke test rather than assuming the
installed JDK proves the full stack works.
[Engines](https://djl.ai/docs/engine.html),
[PyTorch engine](https://djl.ai/engines/pytorch/pytorch-engine/).

## Feasibility assessment and risk mitigation

- The GPU makes compact CNN, LSTM and VAE experiments plausible. This is an
  engineering estimate, not proof of fit or training speed. Start with small
  patches/batches and measure peak memory and duration before scaling.
- Approximately 3.72 GiB free RAM at inspection can constrain compilation and
  data loading. Close unnecessary applications, use low build parallelism and
  stream data; do not preload a complete dataset into memory.
- D: has approximately 20.40 GiB available. Archives, extracted images, build
  caches and CUDA dependencies could exceed this. Measure archive expansion and
  dependency sizes before downloading. E: is an alternative only after choosing
  an authorized project/data location; nothing has been written there.
- PKLot alone advertises a 4.6 GB compressed archive. Start with a small lawful
  subset if the distribution permits; never assume selective archive extraction
  reduces the required download size.
- Train compact models sequentially. Do not promise CPU real-time throughput or
  training a full large detector from scratch on this laptop.
- Semantic masks, vehicle boxes and instance masks need different annotations.
  Data availability may be a larger obstacle than GPU compute.
- Time-series forecasting needs reliable timestamps, capacity and observations
  from consistent views. Sparse dates may permit only limited claims.
- Windows dependencies can work online and fail offline. Cache every artifact,
  disable runtime downloads, and test disconnected execution and fresh builds
  separately. CPU fallback needs its own actual test.

## Dependency and licensing gates

Before pinning dependencies, record exact version, official download URL, archive
hash, architecture, compiler/runtime compatibility, CPU/CUDA choice, unpacked
size and license/notice files. Prefer stable releases; do not copy nightly links
from illustrative installation snippets into the project lock record.

OpenCV 4.5+ uses Apache 2.0 according to its
[license page](https://opencv.org/license/). PyTorch has redistribution and notice
conditions in its [LICENSE](https://github.com/pytorch/pytorch/blob/main/LICENSE).
Archive exact release notices, including bundled third-party terms, later.
No detector implementation or weights have been chosen: review each one's
specific code and weight terms rather than treating all YOLO releases alike.
Dataset attribution does not replace dependency or model-weight permissions.

## Active Python setup proof and remaining gates

1. Verified: standard-library Python data preparation and tests run successfully.
2. Next after the audit: execute a NumPy baseline and Python PyTorch training step; verify parameters change.
3. Repeat on CPU and GPU where supported; record library/runtime versions.
4. Load a local image and save a verified overlay using the chosen Python vision package.
5. Save/reload a checkpoint; verify equivalent predictions.
6. Test the Python environment/notebooks/application with the network disconnected. Record failures honestly.
