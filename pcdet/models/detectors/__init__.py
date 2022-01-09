from .detector3d_template import Detector3DTemplate
from .PartA2_net import PartA2Net
from .point_rcnn import PointRCNN
from .pointpillar import PointPillar
from .pv_rcnn import PVRCNN
from .second_net import SECONDNet
from .second_net_iou import SECONDNetIoU
from .caddn import CaDDN
from .voxel_rcnn import VoxelRCNN
from .centerpoint import CenterPoint
from .centerpoint_kitti import CenterPoint as CenterPointv1
from .centerpoint_rcnn_kitti import CenterPointRCNN as CenterPointRCNNv1
from .centerpoint_once import CenterPoints as CenterPointv2
from .semi_second import SemiSECOND, SemiSECONDIoU
from .CT3D import CT3D
from .CT3D_3CAT import CT3D_3CAT
from .pv_rcnn_plusplus import PVRCNNPlusPlus


__all__ = {
    'Detector3DTemplate': Detector3DTemplate,
    'SECONDNet': SECONDNet,
    'PartA2Net': PartA2Net,
    'PVRCNN': PVRCNN,
    'PointPillar': PointPillar,
    'PointRCNN': PointRCNN,
    'SECONDNetIoU': SECONDNetIoU,
    'CaDDN': CaDDN,
    'VoxelRCNN': VoxelRCNN,
    'CenterPoint': CenterPoint,  # OpenPCDet v0.5.0
    'CenterPointv1': CenterPointv1,  # tianweiy/CenterPoint-KITTI
    'CenterPointRCNN': CenterPointRCNNv1,  # tianweiy/CenterPoint-KITTI
    'CenterPoints': CenterPointv2,  # ONCE_BENCHMARK
    'SemiSECOND': SemiSECOND,
    'SemiSECONDIoU': SemiSECONDIoU,
    'CT3D': CT3D,
    "CT3D_3CAT": CT3D_3CAT,
    'PVRCNNPlusPlus': PVRCNNPlusPlus,
}


def build_detector(model_cfg, num_class, dataset):
    model = __all__[model_cfg.NAME](
        model_cfg=model_cfg, num_class=num_class, dataset=dataset
    )

    return model
