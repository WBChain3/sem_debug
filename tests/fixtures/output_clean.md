The conversion of trained model weights from 32-bit floating-point to 8-bit integer representation is known as post-training quantization. This approach reduces the storage footprint and improves inference latency on edge hardware without requiring access to the original training pipeline.

Large language models contain outlier activation channels that degrade accuracy when weights are quantized to INT8. The narrow dynamic range of 8-bit integers cannot capture the extreme magnitudes found in transformer hidden states.
