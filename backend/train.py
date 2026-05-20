"""
Training script for skin lesion classification model
Supports both healthy vs unhealthy binary classification and multi-class classification
"""

import os
import argparse
from pathlib import Path
from datetime import datetime
import json

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from PIL import Image
import timm
from tqdm import tqdm
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration
class Config:
    """Global configuration wrapper for dataset, model hyperparameters, and execution state.

    Attributes:
        data_dir (Path): Root directory containing SCIN subsets.
        model_name (str): Identifier for the architecture backbone to load from PyTorch image models.
        num_classes (int): Final output size of the custom classification layer.
        img_size (int): Image scaling dimensions (W, H).
    """
    # Data (SCIN: run prepare_scin_data.py → data_scin/train, data_scin/val)
    data_dir = Path("data_scin")
    train_dir = data_dir / "train"
    val_dir = data_dir / "val"
    test_dir = data_dir / "test"
    
    # Model
    model_name = "efficientnet_b0"  # can be changed to efficientnet_b3, resnet50, etc.
    num_classes = 8  # 8 SCIN skin condition categories
    img_size = 224
    pretrained = True
    
    # Training
    batch_size = 32
    num_epochs = 50
    learning_rate = 5e-5
    weight_decay = 1e-4
    num_workers = 4
    
    # Augmentation
    use_augmentation = True
    
    # Device (automatically detects: NVIDIA CUDA, Apple Silicon MPS, or CPU)
    if torch.cuda.is_available():
        device = "cuda"
        gpu_name = torch.cuda.get_device_name(0)
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device = "mps"  # Apple Silicon GPU
        gpu_name = "Apple Silicon"
    else:
        device = "cpu"
        gpu_name = "CPU only"
    
    # Output
    output_dir = Path("models")
    checkpoint_dir = Path("checkpoints")
    log_dir = Path("logs")
    
    # Early stopping
    patience = 10
    min_delta = 1e-4


class SkinLesionDataset(Dataset):
    """PyTorch Dataset wrapper for hierarchically structured image directories.

    Dynamically locates subdirectories and maps them to contiguous integer labels.

    Attributes:
        root_dir (Path): The parent directory containing class sub-folders.
        transform (callable, optional): The transform pipeline applied to the image.
        classes (list[str]): An alphabetical list of class names found.
    """
    
    def __init__(self, root_dir, transform=None, classes=None):
        self.root_dir = Path(root_dir)
        self.transform = transform
        
        # Auto-discover classes from directory structure
        if classes is None:
            self.classes = sorted([d.name for d in self.root_dir.iterdir() if d.is_dir()])
        else:
            self.classes = classes
        
        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}
        
        # Build dataset
        self.samples = []
        for class_name in self.classes:
            class_dir = self.root_dir / class_name
            if not class_dir.exists():
                continue
            
            for img_path in class_dir.glob("*"):
                if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                    self.samples.append((img_path, self.class_to_idx[class_name]))
        
        print(f"Found {len(self.samples)} images in {len(self.classes)} classes")
        print(f"Classes: {self.classes}")
        
        # Count samples per class
        class_counts = {cls: 0 for cls in self.classes}
        for _, label in self.samples:
            class_counts[self.classes[label]] += 1
        print("Class distribution:", class_counts)
    
    def __len__(self):
        """Returns the total number of samples in the dataset."""
        return len(self.samples)
    
    def __getitem__(self, idx):
        """Fetches the image and label for a given index.

        Args:
            idx (int): The index of the sample.

        Returns:
            tuple[torch.Tensor, int]: The transformed image tensor and its corresponding integer label.
        """
        img_path, label = self.samples[idx]
        
        # Load image
        image = Image.open(img_path).convert('RGB')
        
        if self.transform:
            image = self.transform(image)
        
        return image, label


def get_transforms(img_size=224, augment=False):
    """Constructs the Torchvision data transformations for images.

    Args:
        img_size (int, optional): Output size of the resized square images. Defaults to 224.
        augment (bool, optional): Whether to inject random distortion transforms into the training pipeline
                                  to prevent over-fitting. Defaults to False.

    Returns:
        tuple[callable, callable]: The configured training and validation transform pipelines.
    """
    
    # Normalization (ImageNet stats)
    normalize = transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
    
    if augment:
        train_transform = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.5),
            transforms.RandomRotation(20),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
            transforms.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.9, 1.1)),
            transforms.ToTensor(),
            normalize
        ])
    else:
        train_transform = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            normalize
        ])
    
    val_transform = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        normalize
    ])
    
    return train_transform, val_transform


class SkinClassificationModel(nn.Module):
    """Custom wrapper model binding a `timm` feature generator to a bespoke classification head.

    Args:
        model_name (str, optional): `timm` compatible backbone name. Defaults to "efficientnet_b0".
        num_classes (int, optional): Output size for classification. Defaults to 2.
        pretrained (bool, optional): Auto-download ImageNet pre-learned weights. Defaults to True.
        dropout (float, optional): Rate of neuron deactivation for regularization. Defaults to 0.3.
    """
    def __init__(self, model_name="efficientnet_b0", num_classes=2, pretrained=True, dropout=0.3):
        super().__init__()
        
        # Load pretrained backbone
        self.backbone = timm.create_model(
            model_name,
            pretrained=pretrained,
            num_classes=0,  # Remove classification head
            global_pool='avg'
        )
        
        # Get feature dimension
        feat_dim = self.backbone.num_features
        
        # Custom classification head
        self.head = nn.Sequential(
            nn.Linear(feat_dim, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(512, num_classes)
        )
    
    def forward(self, x):
        """Forward pass of the model.

        Args:
            x (torch.Tensor): Input batch of images.

        Returns:
            torch.Tensor: Logits for each class.
        """
        features = self.backbone(x)
        out = self.head(features)
        return out


def train_epoch(model, dataloader, criterion, optimizer, device):
    """Executes a single end-to-end training epoch forward/backward pass.

    Args:
        model (nn.Module): The classification neural network.
        dataloader (DataLoader): Train data stream generator.
        criterion (callable): Loss calculation hook.
        optimizer (optim.Optimizer): Model weight updater hook.
        device (str): Destination hardware identifier (e.g. cuda).

    Returns:
        tuple[float, float]: Epoch average loss and normalized accuracy percentage (0-100).
    """
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    pbar = tqdm(dataloader, desc="Training")
    for images, labels in pbar:
        images, labels = images.to(device), labels.to(device)
        
        # Forward pass
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        # Statistics
        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
        
        pbar.set_postfix({'loss': loss.item(), 'acc': 100. * correct / total})
    
    epoch_loss = running_loss / total
    epoch_acc = 100. * correct / total
    
    return epoch_loss, epoch_acc


def validate(model, dataloader, criterion, device, num_classes=2):
    """Executes inference phase across validation split, producing granular metrics.

    Args:
        model (nn.Module): The compiled neural network.
        dataloader (DataLoader): Validation split stream generator.
        criterion (callable): Loss calculation hook.
        device (str): Destination hardware identifier.
        num_classes (int, optional): Used for ROC AUC calculations. Defaults to 2.

    Returns:
        tuple[float, float, np.ndarray, np.ndarray, float]: Average loss, total accuracy, raw predictions array, actual labels, and calculated ROC AUC score.
    """
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    all_preds = []
    all_labels = []
    all_probs = []
    
    with torch.no_grad():
        pbar = tqdm(dataloader, desc="Validation")
        for images, labels in pbar:
            images, labels = images.to(device), labels.to(device)
            
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            # Get probabilities
            probs = torch.softmax(outputs, dim=1)
            
            running_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
            
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
            
            pbar.set_postfix({'loss': loss.item(), 'acc': 100. * correct / total})
    
    epoch_loss = running_loss / total
    epoch_acc = 100. * correct / total
    
    # Calculate additional metrics
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    all_probs = np.array(all_probs)
    
    # ROC AUC (for binary or one-vs-rest for multi-class)
    try:
        if num_classes == 2:
            roc_auc = roc_auc_score(all_labels, all_probs[:, 1])
        else:
            roc_auc = roc_auc_score(all_labels, all_probs, multi_class='ovr', average='weighted')
    except:
        roc_auc = 0.0
    
    return epoch_loss, epoch_acc, all_preds, all_labels, roc_auc


def plot_confusion_matrix(y_true, y_pred, classes, save_path):
    """Plot and save confusion matrix"""
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes)
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()


def save_training_plots(history, save_dir):
    """Save training history plots"""
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # Loss plot
    plt.figure(figsize=(10, 5))
    plt.plot(history['train_loss'], label='Train Loss')
    plt.plot(history['val_loss'], label='Val Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training and Validation Loss')
    plt.legend()
    plt.grid(True)
    plt.savefig(save_dir / 'loss_plot.png')
    plt.close()
    
    # Accuracy plot
    plt.figure(figsize=(10, 5))
    plt.plot(history['train_acc'], label='Train Acc')
    plt.plot(history['val_acc'], label='Val Acc')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy (%)')
    plt.title('Training and Validation Accuracy')
    plt.legend()
    plt.grid(True)
    plt.savefig(save_dir / 'accuracy_plot.png')
    plt.close()


def main(args):
    """Main training function"""
    config = Config()
    
    # Override config with args
    if args.data_dir:
        config.data_dir = Path(args.data_dir)
        config.train_dir = config.data_dir / "train"
        config.val_dir = config.data_dir / "val"
    if args.batch_size:
        config.batch_size = args.batch_size
    if args.epochs:
        config.num_epochs = args.epochs
    if args.lr:
        config.learning_rate = args.lr
    if args.model:
        config.model_name = args.model
    if args.num_classes is not None:
        config.num_classes = args.num_classes
    
    # Create directories
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    config.log_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if data directories exist
    if not config.train_dir.exists():
        print(f"Error: Training data directory not found: {config.train_dir}")
        print("\nExpected directory structure (SCIN):")
        print("data_scin/")
        print("  train/<condition_name>/*.jpg")
        print("  val/<condition_name>/*.jpg")
        print("\nCreate it from the raw SCIN download:")
        print("  gsutil -m cp -r gs://dx-scin-public-data/dataset scin_data/")
        print("  python prepare_scin_data.py --scin_root ../scin_data --target_dir data_scin")
        print("  python train.py --data_dir data_scin")
        return
    
    # Print device information
    print(f"\n{'='*60}")
    print(f"TRAINING CONFIGURATION")
    print(f"{'='*60}")
    print(f"Device: {config.device.upper()}")
    if config.device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    elif config.device == "mps":
        print(f"GPU: Apple Silicon (Metal Performance Shaders)")
    else:
        print(f"GPU: Not available - using CPU")
    print(f"\nModel: {config.model_name}")
    print(f"Number of classes: {config.num_classes}")
    print(f"Image size: {config.img_size}x{config.img_size}")
    print(f"Batch size: {config.batch_size}")
    print(f"Learning rate: {config.learning_rate}")
    print(f"Epochs: {config.num_epochs}")
    print(f"Workers: {config.num_workers}")
    print(f"{'='*60}\n")
    
    # Get transforms
    train_transform, val_transform = get_transforms(config.img_size, config.use_augmentation)
    
    # Create datasets
    print("\nLoading training data...")
    train_dataset = SkinLesionDataset(config.train_dir, transform=train_transform)
    
    print("\nLoading validation data...")
    val_dataset = SkinLesionDataset(
        config.val_dir,
        transform=val_transform,
        classes=train_dataset.classes  # Use same class order
    )
    
    if args.num_classes is None:
        config.num_classes = len(train_dataset.classes)
        print(f"\nInferred num_classes={config.num_classes} from training folders")
    
    # Create dataloaders
    # Pin memory only for CUDA to speed up transfer to GPU
    use_pin_memory = (config.device == "cuda")
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.batch_size,
        shuffle=True,
        num_workers=config.num_workers,
        pin_memory=use_pin_memory
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=config.num_workers,
        pin_memory=use_pin_memory
    )
    
    # Create model
    print(f"\nCreating model: {config.model_name}")
    model = SkinClassificationModel(
        model_name=config.model_name,
        num_classes=config.num_classes,
        pretrained=config.pretrained
    )
    model = model.to(config.device)
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay
    )
    
    # Learning rate scheduler
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='min',
        factor=0.5,
        patience=5
    )
    
    # Training history
    history = {
        'train_loss': [],
        'train_acc': [],
        'val_loss': [],
        'val_acc': [],
        'val_auc': []
    }
    
    best_val_acc = 0.0
    patience_counter = 0
    
    # Training loop
    print("\nStarting training...")
    for epoch in range(config.num_epochs):
        print(f"\nEpoch {epoch + 1}/{config.num_epochs}")
        print("-" * 50)
        
        # Train
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, config.device)
        
        # Validate
        val_loss, val_acc, val_preds, val_labels, val_auc = validate(
            model, val_loader, criterion, config.device, config.num_classes
        )
        
        # Update scheduler
        scheduler.step(val_loss)
        
        # Save history
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        history['val_auc'].append(val_auc)
        
        print(f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
        print(f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}% | Val AUC: {val_auc:.4f}")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0
            
            # Save model
            checkpoint = {
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_acc,
                'val_loss': val_loss,
                'config': vars(config),
                'classes': train_dataset.classes
            }
            
            torch.save(checkpoint, config.checkpoint_dir / 'best_model.pth')
            torch.save(model.state_dict(), config.output_dir / 'pt_skin_model.pth')
            
            print(f"✓ Saved best model (Val Acc: {val_acc:.2f}%)")
            
            # Save confusion matrix for best model
            plot_confusion_matrix(
                val_labels,
                val_preds,
                train_dataset.classes,
                config.log_dir / 'confusion_matrix_best.png'
            )
            
            # Save classification report
            report = classification_report(
                val_labels,
                val_preds,
                target_names=train_dataset.classes,
                digits=4
            )
            with open(config.log_dir / 'classification_report.txt', 'w') as f:
                f.write(report)
        else:
            patience_counter += 1
        
        # Early stopping
        if patience_counter >= config.patience:
            print(f"\nEarly stopping triggered after {epoch + 1} epochs")
            break
    
    # Save final model
    torch.save(model.state_dict(), config.output_dir / 'pt_skin_model_final.pth')
    
    # Save training plots
    save_training_plots(history, config.log_dir)
    
    # Save training history
    with open(config.log_dir / 'training_history.json', 'w') as f:
        json.dump(history, f, indent=2)
    
    # Save configuration
    config_dict = {
        'model_name': config.model_name,
        'num_classes': config.num_classes,
        'img_size': config.img_size,
        'batch_size': config.batch_size,
        'learning_rate': config.learning_rate,
        'num_epochs': config.num_epochs,
        'best_val_acc': best_val_acc,
        'classes': train_dataset.classes
    }
    
    with open(config.output_dir / 'model_config.json', 'w') as f:
        json.dump(config_dict, f, indent=2)
    
    print("\n" + "=" * 50)
    print("Training completed!")
    print(f"Best validation accuracy: {best_val_acc:.2f}%")
    print(f"Model saved to: {config.output_dir / 'pt_skin_model.pth'}")
    print(f"Logs saved to: {config.log_dir}")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train skin lesion classification model')
    parser.add_argument(
        '--data_dir',
        type=str,
        default='data_scin',
        help='Root with train/ and val/ class subfolders (output of prepare_scin_data.py)',
    )
    parser.add_argument('--batch_size', type=int, help='Batch size for training')
    parser.add_argument('--epochs', type=int, help='Number of epochs')
    parser.add_argument('--lr', type=float, help='Learning rate')
    parser.add_argument('--model', type=str, help='Model architecture (e.g., efficientnet_b0)')
    parser.add_argument(
        '--num_classes',
        type=int,
        default=None,
        help='Number of classes (default: infer from train folder count)',
    )
    
    args = parser.parse_args()
    main(args)
