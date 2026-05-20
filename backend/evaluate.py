"""
Evaluation script for trained model
Test the model on the test set and generate detailed metrics
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms
from pathlib import Path
import numpy as np
import json
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    precision_recall_curve, roc_curve, auc
)
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

# Import from train.py
from train import SkinLesionDataset, SkinClassificationModel, Config


def plot_roc_curves(y_true, y_probs, classes, save_path):
    """Generates and saves Receiver Operating Characteristic (ROC) curves.

    Supports both binary and multi-class (one-vs-rest) evaluation depending on
    the number of configured classes.

    Args:
        y_true (np.ndarray): Array of true class integer labels.
        y_probs (np.ndarray): 2D array of class probability confidences.
        classes (list[str]): List of string names corresponding to the indices.
        save_path (str | Path): Destination file path for the generated plot.
    """
    n_classes = len(classes)
    
    plt.figure(figsize=(10, 8))
    
    if n_classes == 2:
        # Binary classification
        fpr, tpr, _ = roc_curve(y_true, y_probs[:, 1])
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, lw=2, label=f'ROC curve (AUC = {roc_auc:.3f})')
    else:
        # Multi-class (one-vs-rest)
        from sklearn.preprocessing import label_binarize
        y_true_bin = label_binarize(y_true, classes=range(n_classes))
        
        for i in range(n_classes):
            fpr, tpr, _ = roc_curve(y_true_bin[:, i], y_probs[:, i])
            roc_auc = auc(fpr, tpr)
            plt.plot(fpr, tpr, lw=2, label=f'{classes[i]} (AUC = {roc_auc:.3f})')
    
    plt.plot([0, 1], [0, 1], 'k--', lw=2, label='Random')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curves')
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()


def plot_precision_recall_curves(y_true, y_probs, classes, save_path):
    """Generates and saves Precision-Recall evaluation curves.

    Args:
        y_true (np.ndarray): Array of true class integer labels.
        y_probs (np.ndarray): 2D array of class probability confidences.
        classes (list[str]): List of string names corresponding to the indices.
        save_path (str | Path): Destination file path for the generated plot.
    """
    n_classes = len(classes)
    
    plt.figure(figsize=(10, 8))
    
    if n_classes == 2:
        precision, recall, _ = precision_recall_curve(y_true, y_probs[:, 1])
        pr_auc = auc(recall, precision)
        plt.plot(recall, precision, lw=2, label=f'PR curve (AUC = {pr_auc:.3f})')
    else:
        from sklearn.preprocessing import label_binarize
        y_true_bin = label_binarize(y_true, classes=range(n_classes))
        
        for i in range(n_classes):
            precision, recall, _ = precision_recall_curve(y_true_bin[:, i], y_probs[:, i])
            pr_auc = auc(recall, precision)
            plt.plot(recall, precision, lw=2, label=f'{classes[i]} (AUC = {pr_auc:.3f})')
    
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curves')
    plt.legend(loc="lower left")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()


def evaluate_model(model, dataloader, device, classes):
    """Evaluates a loaded model against a test set and produces a granular metrics packet.

    Args:
        model (nn.Module): The compiled classification network.
        dataloader (DataLoader): Data stream for the test partition.
        device (str): Destination hardware identifier.
        classes (list[str]): Ordered list of class labels.

    Returns:
        dict: Evaluation dictionary encompassing raw arrays, aggregated accuracy, 
              ROC_AUC score, and confusion matrix structures.
    """
    model.eval()
    
    all_preds = []
    all_labels = []
    all_probs = []
    
    with torch.no_grad():
        for images, labels in tqdm(dataloader, desc="Evaluating"):
            images = images.to(device)
            
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)
            _, predicted = outputs.max(1)
            
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.numpy())
            all_probs.extend(probs.cpu().numpy())
    
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    all_probs = np.array(all_probs)
    
    # Calculate metrics
    accuracy = 100 * (all_preds == all_labels).sum() / len(all_labels)
    
    # Classification report
    report = classification_report(
        all_labels, all_preds,
        target_names=classes,
        digits=4,
        output_dict=True
    )
    
    # Confusion matrix
    cm = confusion_matrix(all_labels, all_preds)
    
    # ROC AUC
    n_classes = len(classes)
    if n_classes == 2:
        roc_auc = roc_auc_score(all_labels, all_probs[:, 1])
    else:
        try:
            roc_auc = roc_auc_score(all_labels, all_probs, multi_class='ovr', average='weighted')
        except:
            roc_auc = 0.0
    
    return {
        'predictions': all_preds,
        'labels': all_labels,
        'probabilities': all_probs,
        'accuracy': accuracy,
        'classification_report': report,
        'confusion_matrix': cm,
        'roc_auc': roc_auc
    }


def main():
    """Main CLI entry point for executing model evaluation and plotting results."""
    config = Config()
    
    # Print device info
    print(f"\n{'='*60}")
    print(f"MODEL EVALUATION")
    print(f"{'='*60}")
    print(f"Device: {config.device.upper()}")
    if config.device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    elif config.device == "mps":
        print(f"GPU: Apple Silicon (MPS)")
    else:
        print(f"Using CPU")
    print(f"{'='*60}\n")
    
    # Check if test directory exists
    if not config.test_dir.exists():
        print(f"Error: Test directory not found: {config.test_dir}")
        return
    
    # Load model config
    model_config_path = config.output_dir / 'model_config.json'
    if model_config_path.exists():
        with open(model_config_path, 'r') as f:
            model_config = json.load(f)
        classes = model_config['classes']
        num_classes = model_config['num_classes']
        model_name = model_config['model_name']
        print(f"Loaded model config: {model_name} with {num_classes} classes")
    else:
        print("Warning: model_config.json not found, using default config")
        classes = ["healthy", "unhealthy"]
        num_classes = 2
        model_name = config.model_name
    
    # Create evaluation directory
    eval_dir = Path("evaluation")
    eval_dir.mkdir(exist_ok=True)
    
    print(f"Device: {config.device}")
    print(f"Classes: {classes}")
    
    # Load test dataset
    val_transform = transforms.Compose([
        transforms.Resize((config.img_size, config.img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    test_dataset = SkinLesionDataset(
        config.test_dir,
        transform=val_transform,
        classes=classes
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=config.num_workers
    )
    
    # Load model
    print("\nLoading model...")
    model = SkinClassificationModel(
        model_name=model_name,
        num_classes=num_classes,
        pretrained=False
    )
    
    # Load weights
    checkpoint_path = config.checkpoint_dir / 'best_model.pth'
    if checkpoint_path.exists():
        checkpoint = torch.load(checkpoint_path, map_location=config.device)
        model.load_state_dict(checkpoint['model_state_dict'])
        print(f"Loaded best model from epoch {checkpoint['epoch'] + 1}")
        print(f"  Validation accuracy: {checkpoint['val_acc']:.2f}%")
    else:
        # Try loading from output directory
        model_path = config.output_dir / 'pt_skin_model.pth'
        if model_path.exists():
            model.load_state_dict(torch.load(model_path, map_location=config.device))
            print(f"Loaded model from {model_path}")
        else:
            print(f"Error: No trained model found at {checkpoint_path} or {model_path}")
            return
    
    model = model.to(config.device)
    
    # Evaluate
    print("\nEvaluating on test set...")
    results = evaluate_model(model, test_loader, config.device, classes)
    
    # Print results
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"\nTest Accuracy: {results['accuracy']:.2f}%")
    print(f"ROC AUC: {results['roc_auc']:.4f}")
    
    print("\nClassification Report:")
    print("-" * 60)
    report_str = classification_report(
        results['labels'],
        results['predictions'],
        target_names=classes,
        digits=4
    )
    print(report_str)
    
    # Save results
    print("\nSaving results...")
    
    # Save classification report
    with open(eval_dir / 'test_classification_report.txt', 'w') as f:
        f.write(report_str)
    
    # Save confusion matrix plot
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        results['confusion_matrix'],
        annot=True,
        fmt='d',
        cmap='Blues',
        xticklabels=classes,
        yticklabels=classes
    )
    plt.title('Confusion Matrix - Test Set')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(eval_dir / 'confusion_matrix_test.png')
    plt.close()
    
    # Plot ROC curves
    plot_roc_curves(
        results['labels'],
        results['probabilities'],
        classes,
        eval_dir / 'roc_curves.png'
    )
    
    # Plot PR curves
    plot_precision_recall_curves(
        results['labels'],
        results['probabilities'],
        classes,
        eval_dir / 'precision_recall_curves.png'
    )
    
    # Save metrics to JSON
    metrics = {
        'accuracy': float(results['accuracy']),
        'roc_auc': float(results['roc_auc']),
        'classification_report': results['classification_report'],
        'confusion_matrix': results['confusion_matrix'].tolist()
    }
    
    with open(eval_dir / 'test_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"\nResults saved to {eval_dir}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
