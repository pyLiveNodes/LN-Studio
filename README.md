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
1. Install Smart-Studio via pip (or conda if you like): `pip install smart_studio --extra-index-url https://package_puller:8qYs4hBAsmAHJ5AdS_y9@gitlab.csl.uni-bremen.de/api/v4/groups/368/-/packages/pypi/simple`.
2. Run `smart_studio`.
3. Select your livenodes folder (or create a new one).
4. Have fun!

For Development:
1. install Smart-Studio via pip (or conda if you like): `pip install -e . --extra-index-url https://package_puller:8qYs4hBAsmAHJ5AdS_y9@gitlab.csl.uni-bremen.de/api/v4/groups/368/-/packages/pypi/simple`.

### Docs

You can find the docs [here](https://livenodes.pages.csl.uni-bremen.de/smart-studio/index.html).

### Restrictions

None, I switched the conda forge PyQtAds bindings to the [pure python implementation](https://github.com/klauer/qtpydocking/tree/master) of Ken Lauer so that we can use smart_studio with pure pip. 
