## Data

Activation-aware weight quantization and GPTQ address this by identifying the most salient weight groups and retaining higher precision for them during quantization. The remaining parameters are aggressively compressed, yielding a compact model with minimal perplexity increase.

Quantization-aware training incorporates the quantization operation into the training graph itself. This allows the model to learn to compensate for the reduced precision during training, often yielding better accuracy than post-training quantization.

## Methods

SmoothQuant introduces a per-channel scaling transformation that smooths the activation magnitudes before quantization. This technique reduces the impact of outlier channels without requiring retraining or hardware-specific kernels.