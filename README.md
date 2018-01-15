# README

## Overview

Utah teapot for machinic systems

**Problem: get images of pages from books or booklike objects**

Solution(s): 

* Discover and make cameras accessible via channels. Create a virtual equivalent camera to test in absence of hardware.

* Virtual camera has no input. Create a system that generates booklike images to be slurped.

* Press buttons to trigger cameras or slurping sources, make routing flexible enough to experiment.

* Store slurped bytes and define image manipulation pipelines: rotate, crop, ocr

* Tag or classify based on pipeline results(allow more granular sequences or notation of structure)

* Create a reliable set of processes to support large gui's or small cli tools 

* Add sensors, iterate on pressing buttons

## Quickstart

```
git clone https://github.com/galencm/ma
git clone https://github.com/galencm/machinic-env
git clone https://github.com/galencm/machinic-core
git clone https://github.com/galencm/machinic-image
```
**check firewall rules**

Start machines:
```
cd ~/machinic-env
./environment.sh
cd env
./start-machinic-session.sh

cd ~/machinic-core
./regenerate.sh
./start.sh
pytest -v

cd ~/machinic-image
./regenerate.sh
./start.sh
pytest -v
```

Start a primitive generic source:
```
cd ~/machinic-image/generated
python3 slurp-term-cli-6.py run generic

```

Try it out with 2 terminals:

in terminal 1:
```
python3 button-term-curt-4.py
```

in terminal 2:
```
python3 viewer-term-cli-0.py
```

## Contributing

This project uses the C4 process

[https://rfc.zeromq.org/spec:42/C4/](https://rfc.zeromq.org/spec:42/C4/)

## License
Mozilla Public License, v. 2.0 

[http://mozilla.org/MPL/2.0/](http://mozilla.org/MPL/2.0/)


