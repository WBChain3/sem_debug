The conversion of trained model weights from 32-bit floating-point to 8-bit integer representation is known as post-training quantization. This approach reduces the storage footprint and improves inference latency on edge hardware.

A well-known challenge with large language models is the presence of outlier activation channels. These extreme values cause significant accuracy degradation when weights are naively quantized to INT8.

Activation-aware weight quantization and GPTQ address this by identifying the most salient weight groups and retaining higher precision for them during quantization. The remaining parameters are aggressively compressed, yielding a compact model with minimal perplexity increase.

The novel LoRA-XS method factorizes adapter matrices into low-dimensional subspaces, achieving comparable fine-tuning performance with orders of magnitude fewer parameters than standard LoRA approaches. This technique is entirely unrelated to quantization.