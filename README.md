# Smart-Studio

SMART-Studio is a GUI Application to create, run and debug [LiveNode graphs](https://livenodes.pages.csl.uni-bremen.de/livenodes/).
It enables live sensor recording, processing and machine learning for interactive low-latency research applications.

Livenodes are small units of computation for digital signal processing in python. They are connected multiple synced channels to create complex graphs for real-time applications. Each node may provide a GUI or Graph for live interaction and visualization.

Any contribution is welcome! These projects take more time than I can muster, so feel free to create issues for everything that you think might work better and feel free to create a MR for them as well!

Have fun and good coding!
Yale


## Quickstart

I recommend basing your code on the [example project repo](https://gitlab.csl.uni-bremen.de/livenodes/example-project) and adjusting what you need. The project also includes a guide on how to setup Smart-Studio.

To install Smart-Studio:
1. Install PyQTAds: `conda install -c conda-forge pyqtads`
2. install Smart-Studio via pip (or conda if you like): `pip install smart_studio --extra-index-url https://package_puller:8qYs4hBAsmAHJ5AdS_y9@gitlab.csl.uni-bremen.de/api/v4/groups/368/-/packages/pypi/simple`.

## Docs

You can find the docs [here](https://livenodes.pages.csl.uni-bremen.de/smart-studio/index.html).

## Restrictions

- PyQTAds pip install is broken atm -> you'll need to use the conda forge version.
- PyQTAds is only [available for x84_68 systems](https://github.com/conda-forge/pyqtads-feedstock/issues/46). Accordingly Smart-Studio does currntly not run here either (Livenodes and PyQT do tho, so custom interaction tools are possible).
