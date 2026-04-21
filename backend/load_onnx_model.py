"""
Load and use ONNX models for inference

Examples of loading and using ONNX models in different scenarios
"""

import onnxruntime as ort
import numpy as np
from PIL import Image
import json
from pathlib import Path


class ONNXModelWrapper:
    """
    Wrapper class for ONNX model inference.
    Makes it easy to load and use ONNX models.
    """
    
    def __init__(self, onnx_path, use_gpu=False):
        """
        Initialize ONNX model.
        
        Args:
            onnx_path: Path to ONNX model file
            use_gpu: Whether to use GPU acceleration (requires onnxruntime-gpu)
        """
        self.onnx_path = Path(onnx_path)
        
        # Load metadata if available
        metadata_path = self.onnx_path.with_suffix('.json')
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
            self.img_size = self.metadata['img_size']
            self.num_classes = self.metadata['num_classes']
        else:
            # Defaults
            self.img_size = 224
            self.num_classes = 25
        
        # Create ONNX Runtime session
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if use_gpu else ['CPUExecutionProvider']
        self.session = ort.InferenceSession(str(self.onnx_path), providers=providers)
        
        # Get input/output names
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        
        print(f"✓ Loaded ONNX model: {self.onnx_path.name}")
        print(f"  Input: {self.input_name}")
        print(f"  Output: {self.output_name}")
        print(f"  Image size: {self.img_size}x{self.img_size}")
        print(f"  Classes: {self.num_classes}")
    
    def preprocess_image(self, image_path_or_pil):
        """
        Preprocess image for model input.
        
        Args:
            image_path_or_pil: Path to image file or PIL Image object
            
        Returns:
            Preprocessed numpy array ready for inference
        """
        # Load image
        if isinstance(image_path_or_pil, (str, Path)):
            image = Image.open(image_path_or_pil).convert('RGB')
        else:
            image = image_path_or_pil.convert('RGB')
        
        # Resize
        image = image.resize((self.img_size, self.img_size), Image.BILINEAR)
        
        # Convert to array and normalize
        img_array = np.array(image).astype(np.float32) / 255.0
        
        # ImageNet normalization
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_array = (img_array - mean) / std
        
        # Convert to CHW format and add batch dimension
        img_array = np.transpose(img_array, (2, 0, 1))  # HWC -> CHW
        img_array = np.expand_dims(img_array, axis=0)   # Add batch dimension
        
        return img_array
    
    def predict(self, image_path_or_pil):
        """
        Run inference on an image.
        
        Args:
            image_path_or_pil: Path to image file or PIL Image object
            
        Returns:
            Dictionary with predictions and probabilities
        """
        # Preprocess
        img_array = self.preprocess_image(image_path_or_pil)
        
        # Run inference
        outputs = self.session.run(
            [self.output_name],
            {self.input_name: img_array}
        )[0]
        
        # Apply softmax
        logits = outputs[0]
        exp_logits = np.exp(logits - np.max(logits))
        probabilities = exp_logits / exp_logits.sum()
        
        # Get prediction
        predicted_class = int(np.argmax(probabilities))
        confidence = float(probabilities[predicted_class])
        
        # Get top 5
        top5_indices = np.argsort(probabilities)[-5:][::-1]
        top5_probs = probabilities[top5_indices]
        
        return {
            'predicted_class': predicted_class,
            'confidence': confidence,
            'all_probabilities': probabilities.tolist(),
            'top5_classes': top5_indices.tolist(),
            'top5_probabilities': top5_probs.tolist()
        }
    
    def predict_batch(self, image_paths):
        """
        Run inference on multiple images (batch processing).
        
        Args:
            image_paths: List of image paths
            
        Returns:
            List of prediction dictionaries
        """
        results = []
        for img_path in image_paths:
            result = self.predict(img_path)
            results.append(result)
        return results


def example_single_image():
    """Example: Predict on a single image."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Single Image Prediction")
    print("="*70 + "\n")
    
    # Load model
    model = ONNXModelWrapper('models/skin_model.onnx')
    
    # Predict on an image
    test_image = 'data_scin/test/Eczema/example.jpg'  # use any image under data_scin/test/<class>/
    result = model.predict(test_image)
    
    print(f"Image: {test_image}")
    print(f"Predicted class: {result['predicted_class']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"\nTop 5 predictions:")
    for i, (cls, prob) in enumerate(zip(result['top5_classes'], result['top5_probabilities']), 1):
        print(f"  {i}. Class {cls}: {prob:.2%}")


def example_batch_processing():
    """Example: Process multiple images."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Batch Processing")
    print("="*70 + "\n")
    
    from pathlib import Path
    
    # Load model
    model = ONNXModelWrapper('models/skin_model.onnx')
    
    # Get test images
    test_images = list(Path('data_scin/test').rglob('*.jpg'))[:5]
    
    print(f"Processing {len(test_images)} images...\n")
    
    # Process batch
    results = model.predict_batch(test_images)
    
    for img_path, result in zip(test_images, results):
        print(f"{img_path.name:30s} → Class {result['predicted_class']:2d} ({result['confidence']:.1%})")


def example_version_comparison():
    """Example: Compare predictions from different model versions."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Compare Model Versions")
    print("="*70 + "\n")
    
    # Load different model versions
    model_v1 = ONNXModelWrapper('models/skin_model_v1.onnx')
    model_v2 = ONNXModelWrapper('models/skin_model_v2.onnx')
    
    test_image = 'data_scin/test/<YourConditionFolder>/some_image.jpg'
    
    # Get predictions from both
    result_v1 = model_v1.predict(test_image)
    result_v2 = model_v2.predict(test_image)
    
    print(f"Image: {test_image}\n")
    print(f"Model V1:")
    print(f"  Prediction: Class {result_v1['predicted_class']}")
    print(f"  Confidence: {result_v1['confidence']:.2%}")
    
    print(f"\nModel V2:")
    print(f"  Prediction: Class {result_v2['predicted_class']}")
    print(f"  Confidence: {result_v2['confidence']:.2%}")
    
    if result_v1['predicted_class'] == result_v2['predicted_class']:
        print(f"\n✓ Both models agree!")
    else:
        print(f"\n⚠️  Models disagree - may want to investigate")


def example_custom_postprocessing():
    """Example: Custom post-processing of predictions."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Custom Post-Processing")
    print("="*70 + "\n")
    
    # Load model
    model = ONNXModelWrapper('models/skin_model.onnx')
    
    # Load class names (if available)
    class_names = [
        "Acne and Rosacea",
        "Melanoma",
        "Eczema",
        # ... add all 25 classes
    ]
    
    test_image = 'data_scin/test/<YourConditionFolder>/some_image.jpg'
    result = model.predict(test_image)
    
    # Custom logic: Check if high-risk condition
    HIGH_RISK_CLASSES = [1, 2, 5]  # Example: Melanoma, BCC, etc.
    
    predicted_class = result['predicted_class']
    confidence = result['confidence']
    
    if predicted_class in HIGH_RISK_CLASSES and confidence > 0.7:
        urgency = "HIGH - Immediate dermatologist consultation recommended"
    elif confidence > 0.8:
        urgency = "MEDIUM - Schedule appointment within 2 weeks"
    else:
        urgency = "LOW - Monitor and consult if concerned"
    
    print(f"Prediction: {class_names[predicted_class] if predicted_class < len(class_names) else f'Class {predicted_class}'}")
    print(f"Confidence: {confidence:.1%}")
    print(f"Urgency: {urgency}")


if __name__ == "__main__":
    print("ONNX Model Usage Examples")
    print("="*70)
    
    # Run examples
    # Uncomment the ones you want to try
    
    # example_single_image()
    # example_batch_processing()
    # example_version_comparison()
    # example_custom_postprocessing()
    
    print("\nℹ️  Uncomment examples in the code to run them")
    print("   Or import ONNXModelWrapper in your own code:")
    print()
    print("   from load_onnx_model import ONNXModelWrapper")
    print("   model = ONNXModelWrapper('models/skin_model.onnx')")
    print("   result = model.predict('image.jpg')")
