from .anchor_head_multi import AnchorHeadMulti
from .anchor_head_single import AnchorHeadSingle
from .anchor_head_template import AnchorHeadTemplate
from .point_head_box import PointHeadBox
from .point_head_simple import PointHeadSimple
from .point_intra_part_head import PointIntraPartOffsetHead
from .center_head import CenterHead
from .center_head_kitti import CenterHead as CenterHeadv1
from .center_head_once import CenterHead as CenterHeadv2
from .anchor_head_semi import AnchorHeadSemi

__all__ = {
    'AnchorHeadTemplate': AnchorHeadTemplate,
    'AnchorHeadSingle': AnchorHeadSingle,
    'PointIntraPartOffsetHead': PointIntraPartOffsetHead,
    'PointHeadSimple': PointHeadSimple,
    'PointHeadBox': PointHeadBox,
    'AnchorHeadMulti': AnchorHeadMulti,
    'CenterHead': CenterHead,  # OpenPCDet v0.5.0
    'CenterHeadv1': CenterHeadv1,  # tianweiy/CenterPoint-KITTI
    'CenterHeadv2': CenterHeadv2,  # ONCE_BENCHMARK
    'AnchorHeadSemi': AnchorHeadSemi,
}
