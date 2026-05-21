After a model has finished training, quantization compresses its weights by lowering their numeric precision. Moving from FP32 to INT8 cuts the memory footprint by roughly four times and speeds up matrix multiplication on integer-capable accelerators.

Large language models are harder to quantize than convolutional networks because a small fraction of hidden states contain enormous magnitudes. Rounding these outlier activations to the nearest INT8 value destroys model coherence and raises perplexity sharply.

Two popular remedies are GPTQ and AWQ. They mitigate damage by pinpointing the most important one percent of weights and preserving their precision. The remaining ninety-nine percent are aggressively compressed, which keeps the model small while guarding accuracy.