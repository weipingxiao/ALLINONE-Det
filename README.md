# ALLINONE-Det

`ALLINONE-Det` is a general and strong 3D object detection codebase built on [OpenPCDet](https://github.com/open-mmlab/OpenPCDet), which supports more methods, datasets and tools (debugging, recording and analysis). 

## Overview

- [Changelog](#changelog)
- [Supported Features](#Supported-Features)
- [Introduction](#Introduction)
- [Model Zoo](#Model-Zoo)
- [Installation](#Installation)
- [Getting Started](#Getting-Started)
- [Acknowledgement](#Acknowledgement)

## Changelog

[2022-01-08] **NEW:** Update `ALLINONE-Det` to v0.1.0:

- Initial commit

[2022-01-09] **NEW:** Update `ALLINONE-Det` to v0.1.1:

- Support [ONCE dataset](https://once-for-auto-driving.github.io/index.html) and more supervised, semi-supervised, unsupervised domain adaptive learning models for it
- Support spconv 1.0~2.x for `centerpoint_once` detector
- Add PV-RCNN++, Voxel-RCNN related baseline configs on [ONCE dataset](https://once-for-auto-driving.github.io/index.html).

## Supported Features

- [x] Support the latest version of OpenPCDet v0.5.2
- [x] Support KITTI, ONCE, NuScnees, Lyft and Waymo datasets
- [x] Support supervised, semi-supervised, unsupervised domain adaptive learning 
- [x] Support more models and modules than OpenPCDet
- [ ] Support plug-and-play remote visual debugging
- [ ] Support unified model configuration, training, recording and analysis
- [ ] Support Adaptive Object Augmentation Module
- [ ] Support Test Time Augmentation
- [ ] Support Balanced Sample Assignment and Objective Module

## Introduction

## Model Zoo

- Currently supported models: 

  - supervised learning methods (total 11)

  | Methods       | Support datasets             |        Support features        |
  | ------------- | ---------------------------- | :----------------------------: |
  | SECOND        | kitti, once, waymo, nuscenes | `center_head`, `resnet`, `IOU` |
  | PintPillars   | kitti, once, waymo, nuscenes |    `center_head`, `resnet`     |
  | CBGS          | nuscenes, lyft               |                                |
  | PointRCNN     | kitti, once                  |             `IOU`              |
  | Part A^2 Net  | kitti, waymo                 |         `anchor free`          |
  | PV-RCNN       | kitti, once, waymo           |    `center_head`, `resnet`     |
  | PV-RCNN++     | once, waymo                  |    `center_head`, `resnet`     |
  | Voxel-RCNN    | kitti, once, waymo           | `center_head`, `resnet`, `IOU` |
  | CaDDN         | kitti                        |                                |
  | Centerpoint   | kitti, once, waymo, nuscenes |    `center_head`, `resnet`     |
  | PointPainting | once                         |                                |

  - semi-supervised learning methods (total 6)

  | Methods       | Support datasets | Support features |
  | ------------- | ---------------- | :--------------: |
  | SECOND        | once             |                  |
  | Pseudo Label  | once             |                  |
  | Noisy Student | once             |                  |
  | Mean Teacher  | once             |                  |
  | SESS          | once             |                  |
  | 3DIoUMatch    | once             |                  |

  - unsupervised domain adaptation learning methods (total 3)

  | Methods | Support datasets | Support features |
  | ------- | ---------------- | :--------------: |
  | ST3D    | once             |                  |
  | SN      | once             |                  |
  | Oracle  | once             |                  |

## Installation

Please refer to [OpenPCDet](https://github.com/open-mmlab/OpenPCDet/blob/master/docs/INSTALL.md) for the installation of `ALLINONE-Det`.

## Getting Started

## Acknowledgement

Thanks to the strong and flexible [OpenPCDet](https://github.com/open-mmlab/OpenPCDet) codebase maintained by Shaoshuai Shi ([@sshaoshuai](http://github.com/sshaoshuai)) and the reproduced benchmark ([ONCE_Benchmark](https://github.com/PointsCoder/Once_Benchmark)) on the [ONCE](https://once-for-auto-driving.github.io/index.html) (One Million Scenes) dataset by PointsCoder ([@PointsCoder](https://github.com/PointsCoder/)).