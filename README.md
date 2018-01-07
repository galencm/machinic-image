# README

## Overview

A systems Utah teapot for machinic.  

* Problem: get images of pages from books. 

Solution(s): 

* Discover and make cameras accessible via channels. Create a virtual equivalent camera to test in absence of hardware.

* Virtual camera has no input. Create a system that generates booklike images to be slurped.

* Press buttons to trigger cameras or slurping sources, make routing flexible enough to experiment.

* Store slurped bytes and define image manipulation pipelines: rotate,crop,ocr

* Tag or classify based on pipeline results(allow more granular sequences or notation of structure)

* Create a reliable set of processes to support large gui's or small cli tools 


## <a name="quickstart"></a> Quickstart
**Consul & nomad must be running**

**Check firewall rules**

**Core machine must be running**

<a name="quickstart"></a> 
`./ma ./machine_image/ ./machine_image/scanner.xml`

## <a name="test"></a> Testing

##  <a name="contribute"></a> Contributing

This project uses the C4 process 

[https://rfc.zeromq.org/spec:42/C4/](https://rfc.zeromq.org/spec:42/C4/)

##  <a name="license"></a> License
Mozilla Public License, v. 2.0 

[http://mozilla.org/MPL/2.0/](http://mozilla.org/MPL/2.0/)


