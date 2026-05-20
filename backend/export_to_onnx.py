"""
Export PyTorch skin classification model to ONNX format

This script converts your trained PyTorch model to ONNX format for:
- Faster inference
- Cross-platform compatibility
- Model versioning
- Easy deployment
"""

import torch
import torch.onnx
import onnx
import onnxruntime as ort
import numpy as np
from pathlib import Path
import json
from datetime import datetime

from train import SkinClassificationModel, Config


def export_model_to_onnx(
    model_path,
    onnx_path,
    model_name="efficientnet_b0",
    num_classes=10,
    img_size=224,
    opset_version=14,
    verify=True
):
    """Exports a PyTorch model to ONNX format.
    
    Args:
        model_path (str | Path): Path to the PyTorch model (.pth file).
        onnx_path (str | Path): Output path for the ONNX model (.onnx file).
        model_name (str, optional): Architecture name (e.g., 'efficientnet_b0'). Defaults to "efficientnet_b0".
        num_classes (int, optional): Number of output classes. Defaults to 10.
        img_size (int, optional): Input image size. Defaults to 224.
        opset_version (int, optional): ONNX opset version. Defaults to 14.
        verify (bool, optional): Whether to verify the exported model with dummy input. Defaults to True.
        
    Returns:
        tuple[Path, dict]: The Path to the saved ONNX model, and a metadata dictionary.
        
    Raises:
        FileNotFoundError: If the PyTorch model is not found at `model_path`.
    """
    
    print("="*70)
    print("EXPORTING PYTORCH MODEL TO ONNX")
    print("="*70)
    
    # Convert paths to Path objects
    model_path = Path(model_path)
    onnx_path = Path(onnx_path)
    
    # Check if model exists
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    print(f"\n📥 Loading PyTorch model: {model_path}")
    
    # Load model
    model = SkinClassificationModel(
        model_name=model_name,
        num_classes=num_classes,
        pretrained=False
    )
    
    # Load weights
    checkpoint = torch.load(model_path, map_location='cpu')
    if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
        model.load_state_dict(checkpoint['model_state_dict'])
        print(f"  ✓ Loaded from checkpoint (epoch {checkpoint.get('epoch', 'unknown')})")
    else:
        model.load_state_dict(checkpoint)
        print(f"  ✓ Loaded model weights")
    
    model.eval()
    
    # Create dummy input
    dummy_input = torch.randn(1, 3, img_size, img_size)
    
    print(f"\n🔄 Converting to ONNX...")
    print(f"  Input shape: (1, 3, {img_size}, {img_size})")
    print(f"  Output classes: {num_classes}")
    print(f"  ONNX opset: {opset_version}")
    
    # Export to ONNX
    torch.onnx.export(
        model,
        dummy_input,
        str(onnx_path),
        export_params=True,
        opset_version=opset_version,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={
            'input': {0: 'batch_size'},
            'output': {0: 'batch_size'}
        }
    )
    
    print(f"\n✅ Model exported to: {onnx_path}")
    
    # Get file size
    file_size_mb = onnx_path.stat().st_size / (1024 * 1024)
    print(f"  File size: {file_size_mb:.2f} MB")
    
    if verify:
        print(f"\n🔍 Verifying ONNX model...")
        verify_onnx_model(onnx_path, dummy_input, model)
    
    # Save metadata
    metadata = {
        'model_name': model_name,
        'num_classes': num_classes,
        'img_size': img_size,
        'input_shape': [1, 3, img_size, img_size],
        'output_shape': [1, num_classes],
        'opset_version': opset_version,
        'export_date': datetime.now().isoformat(),
        'source_model': str(model_path),
        'file_size_mb': file_size_mb
    }
    
    metadata_path = onnx_path.with_suffix('.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"  ✓ Metadata saved to: {metadata_path}")
    
    return onnx_path, metadata


def verify_onnx_model(onnx_path, dummy_input, original_model=None):
    """Verifies that the ONNX model is valid and produces outputs comparable to PyTorch.

    Args:
        onnx_path (str | Path): Path to the saved ONNX model.
        dummy_input (torch.Tensor): A dummy input tensor to pipe through the models.
        original_model (torch.nn.Module, optional): The original PyTorch model to compare against.

    Returns:
        bool: True if verification successfully completes.
    """
    
    # Check ONNX model validity
    onnx_model = onnx.load(str(onnx_path))
    onnx.checker.check_model(onnx_model)
    print("  ✓ ONNX model structure is valid")
    
    # Create ONNX Runtime session
    ort_session = ort.InferenceSession(str(onnx_path))
    
    # Get input/output info
    input_name = ort_session.get_inputs()[0].name
    output_name = ort_session.get_outputs()[0].name
    
    print(f"  ✓ ONNX Runtime session created")
    print(f"    Input: {input_name}")
    print(f"    Output: {output_name}")
    
    # Run inference with ONNX
    onnx_input = {input_name: dummy_input.numpy()}
    onnx_output = ort_session.run([output_name], onnx_input)[0]
    
    print(f"  ✓ ONNX inference successful")
    print(f"    Output shape: {onnx_output.shape}")
    
    # Compare with PyTorch output if original model provided
    if original_model is not None:
        original_model.eval()
        with torch.no_grad():
            pytorch_output = original_model(dummy_input).numpy()
        
        # Check if outputs are close
        max_diff = np.abs(pytorch_output - onnx_output).max()
        print(f"  ✓ Output comparison:")
        print(f"    Max difference: {max_diff:.6f}")
        
        if max_diff < 1e-5:
            print(f"    ✅ Outputs match perfectly!")
        elif max_diff < 1e-3:
            print(f"    ✅ Outputs are very close (good)")
        else:
            print(f"    ⚠️  Outputs differ (may be acceptable)")
    
    return True


def test_onnx_inference(onnx_path, test_image_path=None):
    """Tests ONNX model inference with either a real image or a random tensor.

    Args:
        onnx_path (str | Path): Path to the ONNX model file.
        test_image_path (str | Path, optional): Path to a test image. If None, a random tensor is used.

    Returns:
        tuple[int, float]: The predicted class index and its confidence probability.
    """
    print("\n" + "="*70)
    print("TESTING ONNX MODEL INFERENCE")
    print("="*70)
    
    # Load metadata
    metadata_path = Path(onnx_path).with_suffix('.json')
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        img_size = metadata['img_size']
        num_classes = metadata['num_classes']
    else:
        img_size = 224
        num_classes = 25
    
    # Create ONNX Runtime session
    ort_session = ort.InferenceSession(str(onnx_path))
    
    if test_image_path:
        from PIL import Image
        import torchvision.transforms as transforms
        
        # Load and preprocess image
        image = Image.open(test_image_path).convert('RGB')
        
        transform = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        img_tensor = transform(image).unsqueeze(0).numpy()
    else:
        # Use random input
        img_tensor = np.random.randn(1, 3, img_size, img_size).astype(np.float32)
        print("\n⚠️  No test image provided, using random input")
    
    # Run inference
    input_name = ort_session.get_inputs()[0].name
    output_name = ort_session.get_outputs()[0].name
    
    import time
    start = time.time()
    outputs = ort_session.run([output_name], {input_name: img_tensor})[0]
    inference_time = (time.time() - start) * 1000
    
    # Get predictions
    probabilities = softmax(outputs[0])
    predicted_class = np.argmax(probabilities)
    confidence = probabilities[predicted_class]
    
    print(f"\n✅ Inference successful!")
    print(f"  Inference time: {inference_time:.2f} ms")
    print(f"  Predicted class: {predicted_class}")
    print(f"  Confidence: {confidence:.2%}")
    print(f"\nTop 3 predictions:")
    top3_indices = np.argsort(probabilities)[-3:][::-1]
    for i, idx in enumerate(top3_indices, 1):
        print(f"  {i}. Class {idx}: {probabilities[idx]:.2%}")
    
    return predicted_class, confidence


def softmax(x):
    """Computes softmax values for a given set of logits.

    Args:
        x (np.ndarray): An array of logit scores.

    Returns:
        np.ndarray: An array of probabilities summing to 1.
    """
    exp_x = np.exp(x - np.max(x))
    return exp_x / exp_x.sum()


def compare_inference_speed(pytorch_model_path, onnx_model_path, num_runs=100):
    """Compares inference speed between PyTorch and ONNX Runtime sequentially.

    Args:
        pytorch_model_path (str | Path): Path to the PyTorch model.
        onnx_model_path (str | Path): Path to the ONNX model.
        num_runs (int, optional): Number of inference passes to benchmark. Defaults to 100.

    Returns:
        dict: Benchmarking results containing averages and speedup multiplier.
    """
    print("\n" + "="*70)
    print("COMPARING INFERENCE SPEED: PYTORCH vs ONNX")
    print("="*70)
    
    import time
    
    # Load PyTorch model
    print("\n📥 Loading PyTorch model...")
    config = Config()
    model = SkinClassificationModel(
        model_name=config.model_name,
        num_classes=config.num_classes,
        pretrained=False
    )
    model.load_state_dict(torch.load(pytorch_model_path, map_location='cpu'))
    model.eval()
    
    # Load ONNX model
    print("📥 Loading ONNX model...")
    ort_session = ort.InferenceSession(str(onnx_model_path))
    input_name = ort_session.get_inputs()[0].name
    output_name = ort_session.get_outputs()[0].name
    
    # Prepare test input
    test_input = torch.randn(1, 3, 224, 224)
    test_input_np = test_input.numpy()
    
    # Warm up
    print(f"\n🔥 Warming up ({num_runs} runs)...")
    with torch.no_grad():
        for _ in range(10):
            _ = model(test_input)
    for _ in range(10):
        _ = ort_session.run([output_name], {input_name: test_input_np})
    
    # Benchmark PyTorch
    print(f"\n⏱️  Benchmarking PyTorch...")
    pytorch_times = []
    with torch.no_grad():
        for _ in range(num_runs):
            start = time.time()
            _ = model(test_input)
            pytorch_times.append((time.time() - start) * 1000)
    
    # Benchmark ONNX
    print(f"⏱️  Benchmarking ONNX...")
    onnx_times = []
    for _ in range(num_runs):
        start = time.time()
        _ = ort_session.run([output_name], {input_name: test_input_np})
        onnx_times.append((time.time() - start) * 1000)
    
    # Results
    pytorch_avg = np.mean(pytorch_times)
    pytorch_std = np.std(pytorch_times)
    onnx_avg = np.mean(onnx_times)
    onnx_std = np.std(onnx_times)
    speedup = pytorch_avg / onnx_avg
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"\nPyTorch:")
    print(f"  Average: {pytorch_avg:.2f} ms (±{pytorch_std:.2f} ms)")
    print(f"  Min: {min(pytorch_times):.2f} ms")
    print(f"  Max: {max(pytorch_times):.2f} ms")
    
    print(f"\nONNX Runtime:")
    print(f"  Average: {onnx_avg:.2f} ms (±{onnx_std:.2f} ms)")
    print(f"  Min: {min(onnx_times):.2f} ms")
    print(f"  Max: {max(onnx_times):.2f} ms")
    
    print(f"\n🚀 Speedup: {speedup:.2f}x faster with ONNX")
    
    if speedup > 1.5:
        print("   ✅ Significant speedup!")
    elif speedup > 1.1:
        print("   ✅ Moderate speedup")
    else:
        print("   ℹ️  Similar performance")
    
    return {
        'pytorch_avg': pytorch_avg,
        'onnx_avg': onnx_avg,
        'speedup': speedup
    }


def main():
    """Main function to export model with various options."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Export PyTorch model to ONNX')
    parser.add_argument('--model', type=str, default='models/pt_skin_model.pth',
                       help='Path to PyTorch model')
    parser.add_argument('--output', type=str, default='models/skin_model.onnx',
                       help='Output ONNX model path')
    parser.add_argument('--model-name', type=str, default='efficientnet_b0',
                       help='Model architecture name')
    parser.add_argument('--num-classes', type=int, default=8,
                       help='Number of output classes')
    parser.add_argument('--img-size', type=int, default=224,
                       help='Input image size')
    parser.add_argument('--opset', type=int, default=14,
                       help='ONNX opset version')
    parser.add_argument('--test-image', type=str, default=None,
                       help='Path to test image for verification')
    parser.add_argument('--benchmark', action='store_true',
                       help='Run speed comparison benchmark')
    parser.add_argument('--no-verify', action='store_true',
                       help='Skip verification')
    
    args = parser.parse_args()
    
    # Export model
    onnx_path, metadata = export_model_to_onnx(
        model_path=args.model,
        onnx_path=args.output,
        model_name=args.model_name,
        num_classes=args.num_classes,
        img_size=args.img_size,
        opset_version=args.opset,
        verify=not args.no_verify
    )
    
    # Test inference
    if args.test_image:
        test_onnx_inference(onnx_path, args.test_image)
    
    # Benchmark
    if args.benchmark:
        compare_inference_speed(args.model, onnx_path)
    
    print("\n" + "="*70)
    print("✅ EXPORT COMPLETE!")
    print("="*70)
    print(f"\nYour ONNX model is ready:")
    print(f"  Model: {onnx_path}")
    print(f"  Metadata: {onnx_path.with_suffix('.json')}")
    print(f"\nTo use in Flask API:")
    print(f"  1. Copy to models/onnx_skin_model.onnx")
    print(f"  2. Restart app.py")
    print(f"  3. It will be automatically detected!")


if __name__ == "__main__":
    main()
