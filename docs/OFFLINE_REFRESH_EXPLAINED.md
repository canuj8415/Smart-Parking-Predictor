# Explaining the offline refresh

This guide describes the work; it does not certify that a student has explained it independently. It stays in the main project and is not automatically included in an already frozen package.

## Source files and installed libraries are different

The export repair changes our Python source. An older copied demonstration still contains its older source bytes, even if the main project is fixed. We therefore create a separately named package and preserve earlier copies. Its manifest records every selected payload path, size, source ID and SHA-256 hash. Generated environments and test outputs are separate from that payload count.

A Python environment provides libraries used by the source. This demonstration uses 107 previously acquired wheel archives with retained notices and publisher metadata. The installer uses `--no-index` and exact version/hash requirements, so it installs from the included files. A fresh environment tests whether this selected copy can install its dependencies without borrowing the main project's installed libraries. Windows, base Python and Tk are still reused. It is not a fully self-contained executable or a fresh-computer test.

## A failed installation is evidence

The first refresh stopped while bootstrapping pip. Its copied files, partial environment, error log and `INCOMPLETE` marker were preserved. That original helper did not retain the failing child's detailed output, so its exact cause was not established. The revised installer invokes the bootstrap explicitly, captures stdout/stderr and gives the child a temporary directory inside the package. Pip's cache is disabled. A new attempt uses a new destination; the installer refuses to overwrite an existing environment.

## Saving a result is a small transaction

An image export contains a picture, its prediction record and checksum metadata. Publishing the picture before the record finishes can leave an incomplete result. The repaired exporter writes into its own staging directory, checks the PNG and hashes, then renames that directory to the final timestamped name. Handled failures clean that attempt's files and preserve previous exports. A separate semantic preview remains separate from the occupancy overlay. Forecast availability must agree with capacity minus occupied counts.

Thirteen synthetic cases test failures, cancellation, invalid values, collisions and complete publication. Their small artificial images and numbers are software fixtures, not real camera observations. Passing them establishes the tested save behavior, not detector accuracy or power-loss recovery.

## Protecting a future forecasting study

The ongoing Singapore study has a reserved future period. A package test must not inspect its target observations early. The refresh selects the exact old snapshot already used by a previous demonstration and checks its original receipt, provider time and hash. Both times must precede the reserved origin period. Selection hashes the opaque file without interpreting its observations. The copied app can then display that earlier, explicitly dated snapshot. This does not validate the learned Singapore forecast or camera occupancy.

## Reading the acceptance evidence

`READY.json` is created only after the build's installation, app, notebook and transaction checks succeed. A directory's existence alone does not mean it is ready. Consult the manifest, validation report and latest pointer. Hidden app checks and a real Jupyter kernel test software routes; manual dialogs, physical disconnection, a new computer, student explanation and official university compliance remain separate acceptance steps.

## 26 October 2026 UTC / copied notebook recovered with approved local loopback

The laterdiagnosticlocalizedthestalltoWindowslocalasyncio socketcreationbeforekernelstart. Withauthorizedloopbackpermission,theunchangedcopiedverifierfinishedin18secondswith1plot;no dependencyreinstall/modelreplaywasneeded. Thelateracceptancerecordlinkstheearlierpassedcomponentsandpreservesoriginalfailures. Thisillustratesanexecution-contextissue,notimprovedmodelaccuracyorstudentmastery.
