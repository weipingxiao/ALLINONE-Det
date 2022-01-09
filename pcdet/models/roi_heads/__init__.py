from .partA2_head import PartA2FCHead
from .pointrcnn_head import PointRCNNHead
from .pvrcnn_head import PVRCNNHead
from .roi_head_template import RoIHeadTemplate
from .voxelrcnn_head import VoxelRCNNHead
from .second_head import SECONDHead
from .semi_second_head import SemiSECONDHead
from .ct3d_head import CT3DHead

__all__ = {
    'RoIHeadTemplate': RoIHeadTemplate,
    'PartA2FCHead': PartA2FCHead,
    'PVRCNNHead': PVRCNNHead,
    'SECONDHead': SECONDHead,
    'PointRCNNHead': PointRCNNHead,
    'VoxelRCNNHead': VoxelRCNNHead,
    'SemiSECONDHead': SemiSECONDHead,
    'CT3DHead': CT3DHead,
}
