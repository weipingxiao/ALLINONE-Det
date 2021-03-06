import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from . import box_utils, common_utils


class SigmoidFocalClassificationLoss(nn.Module):
    """
    Sigmoid focal cross entropy loss.
    """

    def __init__(self, gamma: float = 2.0, alpha: float = 0.25):
        """
        Args:
            gamma: Weighting parameter to balance loss for hard and easy examples.
            alpha: Weighting parameter to balance loss for positive and negative examples.
        """
        super(SigmoidFocalClassificationLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma

    @staticmethod
    def sigmoid_cross_entropy_with_logits(input: torch.Tensor, target: torch.Tensor):
        """ PyTorch Implementation for tf.nn.sigmoid_cross_entropy_with_logits:
            max(x, 0) - x * z + log(1 + exp(-abs(x))) in
            https://www.tensorflow.org/api_docs/python/tf/nn/sigmoid_cross_entropy_with_logits

        Args:
            input: (B, #anchors, #classes) float tensor.
                Predicted logits for each class
            target: (B, #anchors, #classes) float tensor.
                One-hot encoded classification targets

        Returns:
            loss: (B, #anchors, #classes) float tensor.
                Sigmoid cross entropy loss without reduction
        """
        loss = torch.clamp(input, min=0) - input * target + \
               torch.log1p(torch.exp(-torch.abs(input)))
        return loss

    def forward(self, input: torch.Tensor, target: torch.Tensor, weights: torch.Tensor):
        """
        Args:
            input: (B, #anchors, #classes) float tensor.
                Predicted logits for each class
            target: (B, #anchors, #classes) float tensor.
                One-hot encoded classification targets
            weights: (B, #anchors) float tensor.
                Anchor-wise weights.

        Returns:
            weighted_loss: (B, #anchors, #classes) float tensor after weighting.
        """
        pred_sigmoid = torch.sigmoid(input)
        alpha_weight = target * self.alpha + (1 - target) * (1 - self.alpha)
        pt = target * (1.0 - pred_sigmoid) + (1.0 - target) * pred_sigmoid
        focal_weight = alpha_weight * torch.pow(pt, self.gamma)

        bce_loss = self.sigmoid_cross_entropy_with_logits(input, target)

        loss = focal_weight * bce_loss

        if weights.shape.__len__() == 2 or \
                (weights.shape.__len__() == 1 and target.shape.__len__() == 2):
            weights = weights.unsqueeze(-1)

        assert weights.shape.__len__() == loss.shape.__len__()

        return loss * weights


class SigmoidVariFocalClassificationLoss(nn.Module):
    """
    Sigmoid focal cross entropy loss.
    """

    def __init__(self, gamma: float = 2.0, alpha: float = 0.25):
        """
        Args:
            gamma: Weighting parameter to balance loss for hard and easy examples.
            alpha: Weighting parameter to balance loss for positive and negative examples.
        """
        super(SigmoidVariFocalClassificationLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.iou_weighted = True

    @staticmethod
    def sigmoid_cross_entropy_with_logits(input: torch.Tensor, target: torch.Tensor):
        """ PyTorch Implementation for tf.nn.sigmoid_cross_entropy_with_logits:
            max(x, 0) - x * z + log(1 + exp(-abs(x))) in
            https://www.tensorflow.org/api_docs/python/tf/nn/sigmoid_cross_entropy_with_logits

        Args:
            input: (B, #anchors, #classes) float tensor.
                Predicted logits for each class
            target: (B, #anchors, #classes) float tensor.
                One-hot encoded classification targets

        Returns:
            loss: (B, #anchors, #classes) float tensor.
                Sigmoid cross entropy loss without reduction
        """
        loss = torch.clamp(input, min=0) - input * target + \
               torch.log1p(torch.exp(-torch.abs(input)))
        return loss

    def forward(self, input: torch.Tensor, target: torch.Tensor, weights: torch.Tensor):
        """
        Args:
            input: (B, #anchors, #classes) float tensor.
                Predicted logits for each class
            target: (B, #anchors, #classes) float tensor.
                One-hot encoded classification targets
            weights: (B, #anchors) float tensor.
                Anchor-wise weights.

        Returns:
            weighted_loss: (B, #anchors, #classes) float tensor after weighting.
        """
        pred_sigmoid = torch.sigmoid(input)
        # alpha_weight = target * self.alpha + (1 - target) * (1 - self.alpha)
        # pt = target * (1.0 - pred_sigmoid) + (1.0 - target) * pred_sigmoid
        # focal_weight = alpha_weight * torch.pow(pt, self.gamma)

        if self.iou_weighted:
            focal_weight = target * (target > 0.0).float() + \
                           self.alpha * (pred_sigmoid - target).abs().pow(self.gamma) * \
                           (target <= 0.0).float()
        else:
            focal_weight = (target > 0.0).float() + \
                           self.alpha * (pred_sigmoid - target).abs().pow(self.gamma) * \
                           (target <= 0.0).float()

        bce_loss = self.sigmoid_cross_entropy_with_logits(input, target)
        # bce_loss = F.binary_cross_entropy_with_logits(input, target, reduction='none')  # 2021.7.13

        loss = focal_weight * bce_loss

        if weights.shape.__len__() == 2 or \
                (weights.shape.__len__() == 1 and target.shape.__len__() == 2):
            weights = weights.unsqueeze(-1)

        assert weights.shape.__len__() == loss.shape.__len__()

        return loss * weights


class SigmoidQualityFocalClassificationLoss(nn.Module):
    """
        Sigmoid quality focal classificationLoss loss.
        """

    def __init__(self, gamma: float = 2.0, alpha: float = 0.25):
        """
        Args:
            gamma: Weighting parameter to balance loss for hard and easy examples.
        """
        super(SigmoidQualityFocalClassificationLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.pos_neg_weighted = False

    @staticmethod
    def quality_focal_loss(pred, target, beta=2.0):
        r"""Quality Focal Loss (QFL) is from `Generalized Focal Loss: Learning
        Qualified and Distributed Bounding Boxes for Dense Object Detection
        <https://arxiv.org/abs/2006.04388>`_.

        Args:
            pred (torch.Tensor): Predicted joint representation of classification
                and quality (IoU) estimation with shape (N, C), C is the number of
                classes.
            target (tuple([torch.Tensor])): Target category label with shape (N,)
                and target quality label with shape (N,).
            beta (float): The beta parameter for calculating the modulating factor.
                Defaults to 2.0.

        Returns:
            torch.Tensor: Loss tensor with shape (N,).
        """

        # negatives are supervised by 0 quality score
        pred_sigmoid = torch.sigmoid(pred)
        scale_factor = pred_sigmoid
        zerolabel = scale_factor.new_zeros(pred.shape)
        loss = F.binary_cross_entropy_with_logits(
            pred, zerolabel, reduction='none') * scale_factor.pow(beta)

        # positives are supervised by bbox quality (IoU) score
        pos = (target > 0.0)
        scale_factor = target[pos] - pred_sigmoid[pos]
        loss[pos] = F.binary_cross_entropy_with_logits(
            pred[pos], target[pos],
            reduction='none') * scale_factor.abs().pow(beta)

        # ?????????
        # focal_weight = (pred_sigmoid - target).abs().pow(beta) * (target > 0.0).float() + pred_sigmoid.pow(beta) * (target <= 0.0).float()
        # bce_loss = F.binary_cross_entropy_with_logits(pred, target, reduction='none')
        # loss = focal_weight * bce_loss

        return loss

    def forward(self, input: torch.Tensor, target: torch.Tensor, weights: torch.Tensor):
        """
        Args:
            input: (B, #anchors, #classes) float tensor.
                Predicted logits for each class
            target: (B, #anchors, #classes) float tensor.
                One-hot encoded classification targets
            weights: (B, #anchors) float tensor.
                Anchor-wise weights.

        Returns:
            weighted_loss: (B, #anchors, #classes) float tensor after weighting.
        """

        pred_sigmoid = torch.sigmoid(input)

        # ?????????
        # negatives are supervised by 0 quality score
        # scale_factor = pred_sigmoid
        # zerolabel = scale_factor.new_zeros(input.shape)
        # loss = F.binary_cross_entropy_with_logits(
        #     input, zerolabel, reduction='none'
        # ) * scale_factor.pow(self.gamma)

        # positives are supervised by bbox quality (IoU) score
        # pos = (target > 0.0)
        # scale_factor = target[pos] - pred_sigmoid[pos]
        # loss[pos] = F.binary_cross_entropy_with_logits(
        #     input[pos], target[pos], reduction='none'
        # ) * scale_factor.abs().pow(self.gamma)

        # ?????????
        if self.pos_neg_weighted:
            focal_weight = self.alpha * (pred_sigmoid - target).abs().pow(self.gamma) * (target > 0.0).float() + \
                           (1 - self.alpha) * pred_sigmoid.pow(self.gamma) * (target <= 0.0).float()
        else:
            focal_weight = (pred_sigmoid - target).abs().pow(self.gamma) * (target > 0.0).float() + \
                           pred_sigmoid.pow(self.gamma) * (target <= 0.0).float()

        bce_loss = F.binary_cross_entropy_with_logits(input, target, reduction='none')
        loss = focal_weight * bce_loss

        if weights.shape.__len__() == 2 or \
                (weights.shape.__len__() == 1 and target.shape.__len__() == 2):
            weights = weights.unsqueeze(-1)

        assert weights.shape.__len__() == loss.shape.__len__()
        return loss * weights


class WeightedSmoothL1Loss(nn.Module):
    """
    Code-wise Weighted Smooth L1 Loss modified based on fvcore.nn.smooth_l1_loss
    https://github.com/facebookresearch/fvcore/blob/master/fvcore/nn/smooth_l1_loss.py
                  | 0.5 * x ** 2 / beta   if abs(x) < beta
    smoothl1(x) = |
                  | abs(x) - 0.5 * beta   otherwise,
    where x = input - target.
    """
    def __init__(self, beta: float = 1.0 / 9.0, code_weights: list = None):
        """
        Args:
            beta: Scalar float.
                L1 to L2 change point.
                For beta values < 1e-5, L1 loss is computed.
            code_weights: (#codes) float list if not None.
                Code-wise weights.
        """
        super(WeightedSmoothL1Loss, self).__init__()
        self.beta = beta
        if code_weights is not None:
            self.code_weights = np.array(code_weights, dtype=np.float32)
            self.code_weights = torch.from_numpy(self.code_weights).cuda()

    @staticmethod
    def smooth_l1_loss(diff, beta):
        if beta < 1e-5:
            loss = torch.abs(diff)
        else:
            n = torch.abs(diff)
            loss = torch.where(n < beta, 0.5 * n ** 2 / beta, n - 0.5 * beta)

        return loss

    def forward(self, input: torch.Tensor, target: torch.Tensor, weights: torch.Tensor = None):
        """
        Args:
            input: (B, #anchors, #codes) float tensor.
                Ecoded predicted locations of objects.
            target: (B, #anchors, #codes) float tensor.
                Regression targets.
            weights: (B, #anchors) float tensor if not None.

        Returns:
            loss: (B, #anchors) float tensor.
                Weighted smooth l1 loss without reduction.
        """
        target = torch.where(torch.isnan(target), input, target)  # ignore nan targets

        diff = input - target
        # code-wise weighting
        if self.code_weights is not None:
            diff = diff * self.code_weights.view(1, 1, -1)

        loss = self.smooth_l1_loss(diff, self.beta)

        # anchor-wise weighting
        if weights is not None:
            assert weights.shape[0] == loss.shape[0] and weights.shape[1] == loss.shape[1]
            loss = loss * weights.unsqueeze(-1)

        return loss


class WeightedL1Loss(nn.Module):
    def __init__(self, code_weights: list = None):
        """
        Args:
            code_weights: (#codes) float list if not None.
                Code-wise weights.
        """
        super(WeightedL1Loss, self).__init__()
        if code_weights is not None:
            self.code_weights = np.array(code_weights, dtype=np.float32)
            self.code_weights = torch.from_numpy(self.code_weights).cuda()

    def forward(self, input: torch.Tensor, target: torch.Tensor, weights: torch.Tensor = None):
        """
        Args:
            input: (B, #anchors, #codes) float tensor.
                Ecoded predicted locations of objects.
            target: (B, #anchors, #codes) float tensor.
                Regression targets.
            weights: (B, #anchors) float tensor if not None.

        Returns:
            loss: (B, #anchors) float tensor.
                Weighted smooth l1 loss without reduction.
        """
        target = torch.where(torch.isnan(target), input, target)  # ignore nan targets

        diff = input - target
        # code-wise weighting
        if self.code_weights is not None:
            diff = diff * self.code_weights.view(1, 1, -1)

        loss = torch.abs(diff)

        # anchor-wise weighting
        if weights is not None:
            assert weights.shape[0] == loss.shape[0] and weights.shape[1] == loss.shape[1]
            loss = loss * weights.unsqueeze(-1)

        return loss


class WeightedCrossEntropyLoss(nn.Module):
    """
    Transform input to fit the fomation of PyTorch offical cross entropy loss
    with anchor-wise weighting.
    """
    def __init__(self):
        super(WeightedCrossEntropyLoss, self).__init__()

    def forward(self, input: torch.Tensor, target: torch.Tensor, weights: torch.Tensor):
        """
        Args:
            input: (B, #anchors, #classes) float tensor.
                Predited logits for each class.
            target: (B, #anchors, #classes) float tensor.
                One-hot classification targets.
            weights: (B, #anchors) float tensor.
                Anchor-wise weights.

        Returns:
            loss: (B, #anchors) float tensor.
                Weighted cross entropy loss without reduction
        """
        input = input.permute(0, 2, 1)
        target = target.argmax(dim=-1)
        loss = F.cross_entropy(input, target, reduction='none') * weights
        return loss


def get_corner_loss_lidar(pred_bbox3d: torch.Tensor, gt_bbox3d: torch.Tensor):
    """
    Args:
        pred_bbox3d: (N, 7) float Tensor.
        gt_bbox3d: (N, 7) float Tensor.

    Returns:
        corner_loss: (N) float Tensor.
    """
    assert pred_bbox3d.shape[0] == gt_bbox3d.shape[0]

    pred_box_corners = box_utils.boxes_to_corners_3d(pred_bbox3d)
    gt_box_corners = box_utils.boxes_to_corners_3d(gt_bbox3d)

    gt_bbox3d_flip = gt_bbox3d.clone()
    gt_bbox3d_flip[:, 6] += np.pi
    gt_box_corners_flip = box_utils.boxes_to_corners_3d(gt_bbox3d_flip)
    # (N, 8)
    corner_dist = torch.min(torch.norm(pred_box_corners - gt_box_corners, dim=2),
                            torch.norm(pred_box_corners - gt_box_corners_flip, dim=2))
    # (N, 8)
    corner_loss = WeightedSmoothL1Loss.smooth_l1_loss(corner_dist, beta=1.0)

    return corner_loss.mean(dim=1)


def get_gridify_iou3d_loss(gt_bbox3d: torch.Tensor, pred_bbox3d: torch.Tensor, grid_size=10):
    """
    Args:
        gt_bbox3d: (N, 7) float Tensor.
        pred_bbox3d: (N, 7) float Tensor.

    Returns:
        iou3d_loss: (N) float Tensor.
    """
    assert gt_bbox3d.shape[0] == pred_bbox3d.shape[0]
    gt_bbox3d_area = torch.prod(gt_bbox3d[:, 3:6], dim=1)
    pred_bbox3d_area = torch.prod(pred_bbox3d[:, 3:6], dim=1)
    area_per_grid = gt_bbox3d_area / grid_size**3

    # angle alpha
    angle_cos = torch.cos(-1 * pred_bbox3d[:, 6]).unsqueeze(-1)
    angle_sin = torch.sin(-1 * pred_bbox3d[:, 6]).unsqueeze(-1)

    # (N, 7x7x7, 3)
    grid_xyz, _ = get_global_grid_points_of_roi(gt_bbox3d, grid_size)
    dist_grid_to_center = grid_xyz - pred_bbox3d[:, :3].unsqueeze(1)

    dist_x = dist_grid_to_center[:, :, 0]
    dist_y = dist_grid_to_center[:, :, 1]
    dist_z = dist_grid_to_center[:, :, 2]

    rot_dist_x = dist_x * angle_cos + dist_y * (-1 * angle_sin)
    rot_dist_y = dist_y * angle_sin + dist_y * angle_cos
    rot_dist_z = dist_z

    kernel_x = inside_kernel(rot_dist_x, pred_bbox3d[:, 3].unsqueeze(1))
    kernel_y = inside_kernel(rot_dist_y, pred_bbox3d[:, 4].unsqueeze(1))
    kernel_z = inside_kernel(rot_dist_z, pred_bbox3d[:, 5].unsqueeze(1))

    inside_indicator = kernel_x * kernel_y * kernel_z

    inside_num = torch.sum(inside_indicator, dim=1)

    intersect_area = inside_num * area_per_grid

    gridify_iou3d = intersect_area / (gt_bbox3d_area + pred_bbox3d_area - intersect_area)

    loss_iou3d = 1 - gridify_iou3d

    return loss_iou3d


def get_global_grid_points_of_roi(rois, grid_size):
    rois = rois.view(-1, rois.shape[-1])
    batch_size_rcnn = rois.shape[0]

    local_roi_grid_points = get_dense_grid_points(rois, batch_size_rcnn, grid_size)  # (B, 6x6x6, 3)
    global_roi_grid_points = common_utils.rotate_points_along_z(
        local_roi_grid_points.clone(), rois[:, 6]
    ).squeeze(dim=1)
    global_center = rois[:, 0:3].clone()
    global_roi_grid_points += global_center.unsqueeze(dim=1)
    return global_roi_grid_points, local_roi_grid_points


def get_dense_grid_points(rois, batch_size_rcnn, grid_size):
    faked_features = rois.new_ones((grid_size, grid_size, grid_size))
    dense_idx = faked_features.nonzero()  # (N, 3) [x_idx, y_idx, z_idx]
    dense_idx = dense_idx.repeat(batch_size_rcnn, 1, 1).float()  # (B, 6x6x6, 3)

    local_roi_size = rois.view(batch_size_rcnn, -1)[:, 3:6]
    roi_grid_points = (dense_idx + 0.5) / grid_size * local_roi_size.unsqueeze(dim=1) \
                        - (local_roi_size.unsqueeze(dim=1) / 2)  # (B, 6x6x6, 3)
    return roi_grid_points


def inside_kernel(dist, gt_size, scalar=10, eps=1e-8):
    dist_abs = torch.abs(dist + eps)
    half_size = gt_size.float() / 2
    inside_weight = 1 - 1./ (1 + torch.exp(-1 * scalar*(dist_abs - half_size)))
    return inside_weight


# ONCE_BENCHMARK
class CenterNetFocalLoss(nn.Module):
    """nn.Module warpper for focal loss"""
    def __init__(self):
        super(CenterNetFocalLoss, self).__init__()

    def _neg_loss(self, pred, gt):
        """ Modified focal loss. Exactly the same as CornerNet.
            Runs faster and costs a little bit more memory
            Arguments:
              pred (batch x c x h x w)
              gt_regr (batch x c x h x w)
        """
        pos_inds = gt.eq(1).float()
        neg_inds = gt.lt(1).float()

        neg_weights = torch.pow(1 - gt, 4)

        loss = 0

        pos_loss = torch.log(pred) * torch.pow(1 - pred, 2) * pos_inds
        neg_loss = torch.log(1 - pred) * torch.pow(pred, 2) * neg_weights * neg_inds

        num_pos = pos_inds.float().sum()

        pos_loss = pos_loss.sum()
        neg_loss = neg_loss.sum()

        if num_pos == 0:
            loss = loss - neg_loss
        else:
            loss = loss - (pos_loss + neg_loss) / num_pos
        return loss

    def forward(self, out, target):
        return self._neg_loss(out, target)


def _gather_feat(feat, ind, mask=None):
    dim  = feat.size(2)
    ind  = ind.unsqueeze(2).expand(ind.size(0), ind.size(1), dim)
    feat = feat.gather(1, ind)
    if mask is not None:
        mask = mask.unsqueeze(2).expand_as(feat)
        feat = feat[mask]
        feat = feat.view(-1, dim)
    return feat


def _transpose_and_gather_feat(feat, ind):
    feat = feat.permute(0, 2, 3, 1).contiguous()
    feat = feat.view(feat.size(0), -1, feat.size(3)).contiguous()
    feat = _gather_feat(feat, ind)
    return feat.contiguous()


class CenterNetRegLoss(nn.Module):
    """Regression loss for an output tensor
      Arguments:
        output (batch x dim x h x w)
        mask (batch x max_objects)
        ind (batch x max_objects)
        target (batch x max_objects x dim)
    """

    def __init__(self):
        super(CenterNetRegLoss, self).__init__()

    def _reg_loss(self, regr, gt_regr, mask):
        """ L1 regression loss
            Arguments:
            regr (batch x max_objects x dim)
            gt_regr (batch x max_objects x dim)
            mask (batch x max_objects)
        """
        num = mask.float().sum()
        mask = mask.unsqueeze(2).expand_as(gt_regr).float()
        isnotnan = (~ torch.isnan(gt_regr)).float()
        mask *= isnotnan
        regr = regr * mask
        gt_regr = gt_regr * mask

        loss = torch.abs(regr - gt_regr)
        loss = loss.transpose(2, 0).contiguous()

        loss = torch.sum(loss, dim=2)
        loss = torch.sum(loss, dim=1)

        loss = loss / (num + 1e-4)
        return loss

    def forward(self, output, mask, ind, target):
        pred = _transpose_and_gather_feat(output, ind)
        loss = self._reg_loss(pred, target, mask)
        return loss


class CenterNetSmoothRegLoss(nn.Module):
    """Regression loss for an output tensor
      Arguments:
        output (batch x dim x h x w)
        mask (batch x max_objects)
        ind (batch x max_objects)
        target (batch x max_objects x dim)
    """

    def __init__(self):
        super(CenterNetSmoothRegLoss, self).__init__()

    def _smooth_reg_loss(self, regr, gt_regr, mask, sigma=3):
        """ L1 regression loss
          Arguments:
            regr (batch x max_objects x dim)
            gt_regr (batch x max_objects x dim)
            mask (batch x max_objects)
        """
        num = mask.float().sum()
        mask = mask.unsqueeze(2).expand_as(gt_regr).float()
        isnotnan = (~ torch.isnan(gt_regr)).float()
        mask *= isnotnan
        regr = regr * mask
        gt_regr = gt_regr * mask

        abs_diff = torch.abs(regr - gt_regr)

        abs_diff_lt_1 = torch.le(abs_diff, 1 / (sigma ** 2)).type_as(abs_diff)

        loss = abs_diff_lt_1 * 0.5 * torch.pow(abs_diff * sigma, 2) + (
                abs_diff - 0.5 / (sigma ** 2)
        ) * (1.0 - abs_diff_lt_1)

        loss = loss.transpose(2, 0).contiguous()

        loss = torch.sum(loss, dim=2)
        loss = torch.sum(loss, dim=1)

        loss = loss / (num + 1e-4)
        return loss

    def forward(self, output, mask, ind, target, sin_loss):
        assert sin_loss is False
        pred = _transpose_and_gather_feat(output, ind)
        loss = self._smooth_reg_loss(pred, target, mask)
        return loss


# OpenPCDet v0.5.0
def compute_fg_mask(gt_boxes2d, shape, downsample_factor=1, device=torch.device("cpu")):
    """
    Compute foreground mask for images
    Args:
        gt_boxes2d: (B, N, 4), 2D box labels
        shape: torch.Size or tuple, Foreground mask desired shape
        downsample_factor: int, Downsample factor for image
        device: torch.device, Foreground mask desired device
    Returns:
        fg_mask (shape), Foreground mask
    """
    fg_mask = torch.zeros(shape, dtype=torch.bool, device=device)

    # Set box corners
    gt_boxes2d /= downsample_factor
    gt_boxes2d[:, :, :2] = torch.floor(gt_boxes2d[:, :, :2])
    gt_boxes2d[:, :, 2:] = torch.ceil(gt_boxes2d[:, :, 2:])
    gt_boxes2d = gt_boxes2d.long()

    # Set all values within each box to True
    B, N = gt_boxes2d.shape[:2]
    for b in range(B):
        for n in range(N):
            u1, v1, u2, v2 = gt_boxes2d[b, n]
            fg_mask[b, v1:v2, u1:u2] = True

    return fg_mask


def neg_loss_cornernet(pred, gt, mask=None):
    """
    Refer to https://github.com/tianweiy/CenterPoint.
    Modified focal loss. Exactly the same as CornerNet. Runs faster and costs a little bit more memory
    Args:
        pred: (batch x c x h x w)
        gt: (batch x c x h x w)
        mask: (batch x h x w)
    Returns:
    """
    pos_inds = gt.eq(1).float()
    neg_inds = gt.lt(1).float()

    neg_weights = torch.pow(1 - gt, 4)

    loss = 0

    pos_loss = torch.log(pred) * torch.pow(1 - pred, 2) * pos_inds
    neg_loss = torch.log(1 - pred) * torch.pow(pred, 2) * neg_weights * neg_inds

    if mask is not None:
        mask = mask[:, None, :, :].float()
        pos_loss = pos_loss * mask
        neg_loss = neg_loss * mask
        num_pos = (pos_inds.float() * mask).sum()
    else:
        num_pos = pos_inds.float().sum()

    pos_loss = pos_loss.sum()
    neg_loss = neg_loss.sum()

    if num_pos == 0:
        loss = loss - neg_loss
    else:
        loss = loss - (pos_loss + neg_loss) / num_pos
    return loss


class FocalLossCenterNet(nn.Module):
    """
    Refer to https://github.com/tianweiy/CenterPoint
    """
    def __init__(self):
        super(FocalLossCenterNet, self).__init__()
        self.neg_loss = neg_loss_cornernet

    def forward(self, out, target, mask=None):
        return self.neg_loss(out, target, mask=mask)


def _reg_loss(regr, gt_regr, mask):
    """
    Refer to https://github.com/tianweiy/CenterPoint
    L1 regression loss
    Args:
        regr (batch x max_objects x dim)
        gt_regr (batch x max_objects x dim)
        mask (batch x max_objects)
    Returns:
    """
    num = mask.float().sum()
    mask = mask.unsqueeze(2).expand_as(gt_regr).float()
    isnotnan = (~ torch.isnan(gt_regr)).float()
    mask *= isnotnan
    regr = regr * mask
    gt_regr = gt_regr * mask

    loss = torch.abs(regr - gt_regr)
    loss = loss.transpose(2, 0)

    loss = torch.sum(loss, dim=2)
    loss = torch.sum(loss, dim=1)
    # else:
    #  # D x M x B
    #  loss = loss.reshape(loss.shape[0], -1)

    # loss = loss / (num + 1e-4)
    loss = loss / torch.clamp_min(num, min=1.0)
    # import pdb; pdb.set_trace()
    return loss


class RegLossCenterNet(nn.Module):
    """
    Refer to https://github.com/tianweiy/CenterPoint
    """

    def __init__(self):
        super(RegLossCenterNet, self).__init__()

    def forward(self, output, mask, ind=None, target=None):
        """
        Args:
            output: (batch x dim x h x w) or (batch x max_objects)
            mask: (batch x max_objects)
            ind: (batch x max_objects)
            target: (batch x max_objects x dim)
        Returns:
        """
        if ind is None:
            pred = output
        else:
            pred = _transpose_and_gather_feat(output, ind)
        loss = _reg_loss(pred, target, mask)
        return loss