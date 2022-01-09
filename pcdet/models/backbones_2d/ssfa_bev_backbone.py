import numpy as np
import torch
import torch.nn as nn


# 2021.8.28
# CIA-SSD (AAAI 2021)
class SSFABEVBackbone(nn.Module):
    def __init__(self, model_cfg, input_channels):
        super().__init__()
        self.model_cfg = model_cfg

        if self.model_cfg.get('LAYER_NUMS', None) is not None:
            assert len(self.model_cfg.LAYER_NUMS) == len(self.model_cfg.LAYER_STRIDES) == len(self.model_cfg.NUM_FILTERS)
            layer_nums = self.model_cfg.LAYER_NUMS
            layer_strides = self.model_cfg.LAYER_STRIDES
            num_filters = self.model_cfg.NUM_FILTERS
        else:
            layer_nums = layer_strides = num_filters = []

        if self.model_cfg.get('UPSAMPLE_STRIDES', None) is not None:
            assert len(self.model_cfg.UPSAMPLE_STRIDES) == len(self.model_cfg.NUM_UPSAMPLE_FILTERS)
            num_upsample_filters = self.model_cfg.NUM_UPSAMPLE_FILTERS
            upsample_strides = self.model_cfg.UPSAMPLE_STRIDES
        else:
            upsample_strides = num_upsample_filters = []

        self.bottom_up_block_0 = nn.Sequential(
            nn.ZeroPad2d(1),
            nn.Conv2d(input_channels, 128, 3, stride=1, bias=False),
            nn.BatchNorm2d(128, eps=1e-3, momentum=0.01),
            nn.ReLU(),

            nn.Conv2d(in_channels=128, out_channels=128, kernel_size=3, stride=1, padding=1, bias=False, ),
            nn.BatchNorm2d(128, eps=1e-3, momentum=0.01),
            nn.ReLU(),

            nn.Conv2d(in_channels=128, out_channels=128, kernel_size=3, stride=1, padding=1, bias=False, ),
            nn.BatchNorm2d(128, eps=1e-3, momentum=0.01),
            nn.ReLU(),
        )

        self.bottom_up_block_1 = nn.Sequential(
            # [200, 176] -> [100, 88]
            nn.Conv2d(in_channels=128, out_channels=256, kernel_size=3, stride=2, padding=1, bias=False, ),
            nn.BatchNorm2d(256, eps=1e-3, momentum=0.01),
            nn.ReLU(),

            nn.Conv2d(in_channels=256, out_channels=256, kernel_size=3, stride=1, padding=1, bias=False, ),
            nn.BatchNorm2d(256, eps=1e-3, momentum=0.01),
            nn.ReLU(),

            nn.Conv2d(in_channels=256, out_channels=256, kernel_size=3, stride=1, padding=1, bias=False, ),
            nn.BatchNorm2d(256, eps=1e-3, momentum=0.01),
            nn.ReLU(),

        )

        self.trans_0 = nn.Sequential(
            nn.Conv2d(in_channels=128, out_channels=128, kernel_size=1, stride=1, padding=0, bias=False, ),
            nn.BatchNorm2d(128, eps=1e-3, momentum=0.01),
            nn.ReLU(),
        )

        self.trans_1 = nn.Sequential(
            nn.Conv2d(in_channels=256, out_channels=256, kernel_size=1, stride=1, padding=0, bias=False, ),
            nn.BatchNorm2d(256, eps=1e-3, momentum=0.01),
            nn.ReLU(),
        )

        self.deconv_block_0 = nn.Sequential(
            nn.ConvTranspose2d(in_channels=256, out_channels=128, kernel_size=3, stride=2, padding=1, output_padding=1, bias=False, ),
            nn.BatchNorm2d(128, eps=1e-3, momentum=0.01),
            nn.ReLU(),
        )

        self.deconv_block_1 = nn.Sequential(
            nn.ConvTranspose2d(in_channels=256, out_channels=128, kernel_size=3, stride=2, padding=1, output_padding=1,
                               bias=False, ),
            nn.BatchNorm2d(128, eps=1e-3, momentum=0.01),
            nn.ReLU(),
        )

        self.conv_0 = nn.Sequential(
            nn.Conv2d(in_channels=128, out_channels=128, kernel_size=3, stride=1, padding=1, bias=False, ),
            nn.BatchNorm2d(128, eps=1e-3, momentum=0.01),
            nn.ReLU(),
        )

        self.w_0 = nn.Sequential(
            nn.Conv2d(in_channels=128, out_channels=1, kernel_size=1, stride=1, padding=0, bias=False, ),
            nn.BatchNorm2d(1, eps=1e-3, momentum=0.01),
        )

        self.conv_1 = nn.Sequential(
            nn.Conv2d(in_channels=128, out_channels=128, kernel_size=3, stride=1, padding=1, bias=False, ),
            nn.BatchNorm2d(128, eps=1e-3, momentum=0.01),
            nn.ReLU(),
        )

        self.w_1 = nn.Sequential(
            nn.Conv2d(in_channels=128, out_channels=1, kernel_size=1, stride=1, padding=0, bias=False, ),
            nn.BatchNorm2d(1, eps=1e-3, momentum=0.01),
        )

        self.num_bev_features = 128

    def forward(self, data_dict):
        """
        Args:
            data_dict:
                spatial_features
        Returns:
        """
        spatial_features = data_dict['spatial_features']
        ups = []
        ret_dict = {}
        x = spatial_features

        x_0 = self.bottom_up_block_0(x)
        x_1 = self.bottom_up_block_1(x_0)
        x_trans_0 = self.trans_0(x_0)
        x_trans_1 = self.trans_1(x_1)
        x_middle_0 = self.deconv_block_0(x_trans_1) + x_trans_0
        x_middle_1 = self.deconv_block_1(x_trans_1)
        x_output_0 = self.conv_0(x_middle_0)
        x_output_1 = self.conv_1(x_middle_1)

        x_weight_0 = self.w_0(x_output_0)
        x_weight_1 = self.w_1(x_output_1)
        x_weight = torch.softmax(torch.cat([x_weight_0, x_weight_1], dim=1), dim=1)
        x_output = x_output_0 * x_weight[:, 0:1, :, :] + x_output_1 * x_weight[:, 1:, :, :]

        data_dict['spatial_features_2d'] = x_output

        return data_dict
