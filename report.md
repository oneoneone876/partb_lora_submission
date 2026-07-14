# Part B Report

## 1. Task Summary

This project fine-tunes Gemma 3 270M with LoRA to generate complete SVG logo documents from detailed visual prompts. The goal is to improve over the 270M base model, not to match Sonnet-level logo quality.

## 2. Reward Design

`reward.py` scores SVG validity, structure, geometry, palette quality, prompt fidelity, and degeneracy penalties. Validity is weighted highest because small models often fail at producing parseable SVG. Structure rewards a reasonable number of vector primitives. Geometry discourages coordinates far outside the `0 0 256 256` canvas. Palette rewards explicit fill/stroke styling and a small cohesive color set. Prompt fidelity checks lightweight color and shape term coverage.

## 3. Training Setup

- Base model: Gemma 3 270M.
- Fine-tuning: LoRA.
- LoRA rank: 8.
- LoRA alpha: 16.
- Dropout: 0.05.
- Learning rate: `2e-4`.
- Epochs: up to 8.
- Loss: assistant SVG tokens only.
- Evaluation decoding: greedy, fixed `max_new_tokens`.

## 4. Self-Evaluation Results

Fill after running training and evaluation.

| Model | Mean Reward | Validity | Structure | Geometry | Palette | Prompt Fidelity |
|---|---:|---:|---:|---:|---:|---:|
| Base Gemma 3 270M | TODO | TODO | TODO | TODO | TODO | TODO |
| LoRA model | TODO | TODO | TODO | TODO | TODO | TODO |
| Delta | TODO | TODO | TODO | TODO | TODO | TODO |

## 5. Example Comparisons

Add 2-3 validation examples after `base_eval.json` and `lora_eval.json` are generated.

## 6. Analysis

The most likely improvement is SVG validity and output discipline. Prompt fidelity may improve less because 270M parameters is small for long structured SVG generation. If reward improves but examples are generic, that indicates a Goodhart effect: the model learned the proxy more than the actual visual task.

## 7. Conclusion

The final conclusion should report whether LoRA improved over the base model and where the proxy reward did or did not align with observed logo quality.

