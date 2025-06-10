[![Format and Test](https://github.com/pyLiveNodes/LN-Studio/actions/workflows/format_test.yml/badge.svg)](https://github.com/pyLiveNodes/LN-Studio/actions/workflows/format_test.yml)
[![Publish](https://github.com/pyLiveNodes/LN-Studio/actions/workflows/publish.yml/badge.svg)](https://github.com/pyLiveNodes/LN-Studio/actions/workflows/publish.yml)

# LN-Studio

LN-Studio is a GUI Application to create, run and debug [LiveNode graphs](https://livenodes.pages.csl.uni-bremen.de/livenodes/).
It enables live sensor recording, processing and machine learning for interactive low-latency research applications.

Livenodes are small units of computation for digital signal processing in python. They are connected multiple synced channels to create complex graphs for real-time applications. Each node may provide a GUI or Graph for live interaction and visualization.

Any contribution is welcome! These projects take more time than I can muster, so feel free to create issues for everything that you think might work better and feel free to create a MR for them as well!

Have fun and good coding!

Yale

## Citation

If you use LN-Studio in your research, please cite it as follows:

As of 2024 there is no dedicated paper to LiveNodes yet. I'm working on it. But for now, please cite the following paper:
```
@inproceedings{hartmann2022demo,
  title = {Interactive and Interpretable Online Human Activity Recognition},
  author = {Hartmann, Yale and Liu, Hui and Schultz, Tanja},
  booktitle = {PERCOM 2022 - 20th IEEE International Conference on Pervasive Computing and Communications Workshops and other Affiliated Events (PerCom Workshops)},
  year = {2022},
  pages = {109--111},
  doi = {10.1109/PerComWorkshops53856.2022.9767207},
  url = {https://www.csl.uni-bremen.de/cms/images/documents/publications/HartmannLiuSchultz_PERCOM2022.pdf},
}
```

## Quickstart

I recommend basing your code on the [example project repo](https://gitlab.csl.uni-bremen.de/livenodes/example-project) and adjusting what you need. The project also includes a guide on how to setup LN-Studio.

To install LN-Studio:
1. Install LN-Studio via pip (or conda if you like): `pip install ln_studio `.
2. Run `ln_studio`.
3. Select your livenodes folder (or create a new one).
4. Have fun!

For Development:
1. install LN-Studio via pip (or conda if you like): `pip install -e . `.

## Migration from 0.9.4

Moving from 0.9 to 0.10 includes refactoring of the project structure. The following steps are necessary to migrate your project:
In your **project folder (the one where ln_studio_state.json is located)**, run `ln_studio_migrate` to migrate your project to the new structure.`

### Docs

You can find the docs [here](https://livenodes.pages.csl.uni-bremen.de/LN-Studio/index.html).

### Restrictions

None, I switched the conda forge PyQtAds bindings to the [pure python implementation](https://github.com/klauer/qtpydocking/tree/master) of Ken Lauer so that we can use ln_studio with pure pip. 
