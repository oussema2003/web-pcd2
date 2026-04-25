import torch
import torch.nn as nn
import math
import timm

# ==========================================
# 3. ARCHITECTURE DU MODÈLE
# ==========================================
class XceptionCNN(nn.Module):
    def __init__(self, pretrained=True):
        super().__init__()
        self.model = timm.create_model('xception', pretrained=pretrained)
        self.model.fc = nn.Identity()
        self.out_features = 2048

    def forward(self, x):
        return self.model(x)

class EfficientNetCNN(nn.Module):
    def __init__(self, model_name='efficientnet_b4', pretrained=True):
        super().__init__()
        self.model = timm.create_model(model_name, pretrained=pretrained)
        self.model.classifier = nn.Identity()
        self.out_features = 1792

    def forward(self, x):
        return self.model(x)

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x):
        return x + self.pe[:, :x.size(1), :]

class CNN_Transformer_Deepfake(nn.Module):
    def __init__(
        self,
        xception_feat_dim=2048,
        efficient_feat_dim=1792,
        transformer_dim=512,
        num_heads=8,
        num_layers=3,
        num_classes=1,
        freeze_ratio=0.7,
        dropout_p=0.4
    ):
        super().__init__()
        self.xception = XceptionCNN(pretrained=False) # Pretrained=False car on charge TES poids plus tard
        self.efficient = EfficientNetCNN(pretrained=False)

        self._freeze_partial(self.xception.model, freeze_ratio)
        self._freeze_partial(self.efficient.model, freeze_ratio)

        combined_dim = xception_feat_dim + efficient_feat_dim
        self.feature_projection = nn.Sequential(
            nn.Linear(combined_dim, transformer_dim),
            nn.GELU(),
            nn.LayerNorm(transformer_dim),
            nn.Dropout(dropout_p)
        )

        self.pos_encoder = PositionalEncoding(transformer_dim)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=transformer_dim, nhead=num_heads,
            dim_feedforward=transformer_dim * 4, dropout=dropout_p,
            activation="gelu", batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        self.classifier = nn.Sequential(
            nn.Linear(transformer_dim, 128),
            nn.GELU(),
            nn.Dropout(dropout_p),
            nn.Linear(128, num_classes)
        )

    def _freeze_partial(self, model, freeze_ratio):
        total_params = sum(1 for _ in model.parameters())
        freeze_until = int(total_params * freeze_ratio)
        for i, param in enumerate(model.parameters()):
            if i < freeze_until:
                param.requires_grad = False
            else:
                param.requires_grad = True

    def forward(self, x_seq):
        batch, seq_len, C, H, W = x_seq.size()
        x_cnn = x_seq.view(batch * seq_len, C, H, W)

        feat_xcep = self.xception(x_cnn)
        feat_eff = self.efficient(x_cnn)

        fused = torch.cat([feat_xcep, feat_eff], dim=1)
        fused = fused.view(batch, seq_len, -1)

        projected_features = self.feature_projection(fused)
        transformer_input = self.pos_encoder(projected_features)
        transformer_out = self.transformer(transformer_input)

        pooled_out = transformer_out.mean(dim=1)
        out = self.classifier(pooled_out)
        return out