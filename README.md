# ALLINONE-Det

`ALLINONE-Det` is a general and strong 3D object detection codebase built on [OpenPCDet](https://github.com/open-mmlab/OpenPCDet), which supports more methods, datasets and tools (debugging, recording and analysis). 

## Overview

- [Changelog](#changelog)
- [Supported Features](#Supported-Features)
- [Model Zoo](#Model-Zoo)
- [Installation](#Installation)
- [Getting Started](#Getting-Started)
- [Acknowledgement](#Acknowledgement)

## Changelog

[2022-01-08] **NEW:** Update `ALLINONE-Det` to v0.1.0:

- Initial commit

## Supported Features

- [x] Support the latest version of OpenPCDet v0.5.2
- [ ] Support KITTI, ONCE, NuScnees, Lyft and Waymo datasets
- [ ] Support more models and modules than OpenPCDet, e.g., CT3D, LiDAR R-CNN, VarifocalLoss, ATSS
- [ ] Support plug-and-play remote visual debugging
- [ ] Support unified model configuration, training, recording and analysis
- [ ] Support Adaptive Object Augmentation Module
- [ ] Support Balanced Sample Assignment and Objective Module
- [ ] Support Test Time Augmentation

## Model Zoo

## Installation

Please refer to [OpenPCDet](https://github.com/open-mmlab/OpenPCDet/blob/master/docs/INSTALL.md) for the installation of `ALLINONE-Det`.

## Getting Started

## Acknowledgement

Thanks to the strong and flexible [OpenPCDet](https://github.com/open-mmlab/OpenPCDet) codebase maintained by Shaoshuai Shi ([@sshaoshuai](http://github.com/sshaoshuai)) and the reproduced benchmark ([ONCE_Benchmark](https://github.com/PointsCoder/Once_Benchmark)) on the [ONCE](https://once-for-auto-driving.github.io/index.html) (One Million Scenes) dataset by PointsCoder ([@PointsCoder](https://github.com/PointsCoder/)).