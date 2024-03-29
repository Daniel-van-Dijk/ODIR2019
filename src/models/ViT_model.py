import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
from torchvision import transforms, models
import pandas as pd
from torch.utils.data import Dataset, DataLoader, SubsetRandomSampler
from PIL import Image
import os
from torchvision import datasets
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
import torchvision.transforms as transforms
import timm
from sklearn import metrics
from sklearn.model_selection import train_test_split
from tqdm.notebook import tqdm
import numpy as np
import torchvision.models as models
from torch.optim.lr_scheduler import ReduceLROnPlateau
import csv
import datetime
from src.models.foundational_model.util.datasets import *
from src.models.foundational_model.util.asymmetric_loss import *
from collections import namedtuple


low_quality_files = [
"2174_right.jpg",
"2175_left.jpg",
"2176_left.jpg",
"2177_left.jpg",
"2177_right.jpg",
"2178_right.jpg",
"2179_left.jpg",
"2179_right.jpg",
"2180_left.jpg",
"2180_right.jpg",
"2181_left.jpg",
"2181_right.jpg",
"2182_left.jpg",
"2182_right.jpg",
"2957_left.jpg",
"2957_right.jpg",
"2340_lef.jpg",
"1706_left.jpg",
"1710_right.jpg",
"4522_left.jpg",
"1222_right.jpg", 
"1260_left.jpg", 
"2133_right.jpg", 
"240_left.jpg",
"240_right.jpg",
"150_left.jpg", 
"150_right.jpg",
]
# Manual found low quality: 2340 left, 1706_left, 1710_right, 4522_left, 1222_right, 1260_left
# 2133_right, 240_left, 240_right, 150_left, 150_right


"""
class ODIRDataset(Dataset):
    def __init__(self, dataframe, img_dir, transforms=None):
        self.dataframe = dataframe
        self.img_dir = img_dir
        self.transforms = transforms

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, idx):
        left_img_name = os.path.join(self.img_dir, self.dataframe.iloc[idx]['Left-Fundus'])
        right_img_name = os.path.join(self.img_dir, self.dataframe.iloc[idx]['Right-Fundus'])

        left_image = Image.open(left_img_name)
        right_image = Image.open(right_img_name)

        values = self.dataframe.iloc[idx][5:].values.astype(np.float32)
        labels = torch.tensor(values)

        if self.transforms:
            left_image = self.transforms(left_image)
            right_image = self.transforms(right_image)

        return (left_image, right_image), labels

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),])
"""

disease_columns = ['N', 'D', 'G', 'C', 'A', 'H', 'M', 'O']
original_df = pd.read_excel('/home/scur0547/ODIR2019/data/ODIR-5K_Training_Annotations(Updated)_V2.xlsx')
original_df = original_df.drop(columns=['Left-Diagnostic Keywords', 'Right-Diagnostic Keywords'])

low_quality_files_set = set(low_quality_files)


original_df = original_df[~original_df['Left-Fundus'].isin(low_quality_files_set) & ~original_df['Right-Fundus'].isin(low_quality_files_set)]


train_df, validation_df = train_test_split(original_df, test_size=0.2, random_state=42)


Args = namedtuple('Args', ['input_size'])
args = Args(input_size=224)

dataset_train = ODIRDataset2eye(train_df, '/home/scur0547/ODIR2019/data/cropped_ODIR-5K_Training_Dataset', is_train=True, args=args)
dataset_val = ODIRDataset2eye(validation_df, '/home/scur0547/ODIR2019/data/cropped_ODIR-5K_Training_Dataset', is_train=False, args=args)


train_dataloader = DataLoader(dataset_train, batch_size=64, shuffle=True)
validation_dataloader = DataLoader(dataset_val, batch_size=64, shuffle=False)

first_batch = next(iter(train_dataloader))

# put annotations in current directory
#df = pd.read_excel('data/ODIR-5K_Training_Annotations(Updated)_V2.xlsx')
#df = df.drop(columns=['Left-Diagnostic Keywords', 'Right-Diagnostic Keywords'])


#train_df, validation_df = train_test_split(df, test_size=0.10, random_state=42)

#train_dataset = ODIRDataset(train_df, 'data/cropped_ODIR-5K_Training_Images', transforms=transform)
#validation_dataset = ODIRDataset(validation_df, 'data/cropped_ODIR-5K_Training_Images', transforms=transform)

#train_dataloader = DataLoader(train_dataset, batch_size=128, shuffle=True)
#validation_dataloader = DataLoader(validation_dataset, batch_size=128, shuffle=False)


class VisionTransformer(nn.Module):
    def __init__(self, num_classes):
        super(VisionTransformer, self).__init__()
        self.num_classes = num_classes

        # Vision Transformer backbone
        self.backbone = timm.create_model('vit_base_patch16_224', pretrained=True)

        # Replace the final classification layer
        self.backbone.head = nn.Identity()

        # Add a classification head for multi-label classification
        self.classification_head = nn.Linear(self.backbone.embed_dim * 2, num_classes)


    def forward(self, image_left, image_right):
        features_left = self.backbone(image_left)
        features_right = self.backbone(image_right)
        combined_features = torch.cat((features_left, features_right), dim=1)

        # Pass through the classification head
        logits = self.classification_head(combined_features)

        return logits

# Define training and evaluation functions
def train(model, dataloader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0

    for batch in tqdm(dataloader):
        (images_left, images_right), labels = batch
        images_left, images_right, labels = images_left.to(device), images_right.to(device), labels.to(device)

        optimizer.zero_grad()
        logits = model(images_left, images_right)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

    return running_loss / len(dataloader)


#calculate kappa, F-1 socre and AUC value
def ODIR_Metrics(gt_data, pr_data):
    th = 0.5
    gt = gt_data.flatten()
    pr = pr_data.flatten()
    kappa = metrics.cohen_kappa_score(gt, pr>th)
    f1 = metrics.f1_score(gt, pr>th, average='micro')
    auc = metrics.roc_auc_score(gt, pr)
    final_score = (kappa+f1+auc)/3.0
    return kappa, f1, auc, final_score

def evaluate(model, dataloader, device, criterion):
    model.eval()
    all_labels = []
    all_logits = []
    val_loss = 0
    with torch.no_grad():
        for (images_left, images_right), labels in tqdm(dataloader):
            images_left, images_right = images_left.to(device), images_right.to(device)
            labels = labels.to(device)

            logits = model(images_left, images_right)
            loss = criterion(logits, labels)
            val_loss += loss.item()
            all_labels.append(labels.cpu().numpy())
            all_logits.append(logits.detach().cpu().numpy())

    all_labels = np.vstack(all_labels)
    all_logits = np.vstack(all_logits)

    all_preds = (all_logits > 0.5).astype(np.float32)

    kappa, f1, auc, final_score = ODIR_Metrics(all_labels, all_preds)

    return val_loss / len(dataloader), final_score, kappa, f1, auc


def check_trainable_parameters(model):
    trainable_params = []
    frozen_params = []

    for name, param in model.named_parameters():
        if param.requires_grad:
            trainable_params.append((name, param.numel()))
        else:
            frozen_params.append((name, param.numel()))

    print("Trainable Parameters:")
    for name, numel in trainable_params:
        print(f"{name}: {numel} parameters")

    print("\nFrozen Parameters:")
    for name, numel in frozen_params:
        print(f"{name}: {numel} parameters")


# Hyperparameters
learning_rate = 0.0001
num_epochs = 50
num_classes = 8  # Number of diseases

# Initialize the model and optimizer
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = VisionTransformer(num_classes).to(device)
model.backbone.requires_grad_(False)
check_trainable_parameters(model)
optimizer = optim.Adam(model.parameters(), lr=learning_rate)
criterion=AsymmetricLoss(gamma_neg=2, gamma_pos=2, clip=0)
#criterion = nn.BCEWithLogitsLoss()  # Binary Cross-Entropy Loss for multi-label classification

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
model_checkpoint_name = f'best_model_{timestamp}.pth'

best_score = -1
scheduler = ReduceLROnPlateau(optimizer, 'min', factor=0.5, patience=5, verbose=True)
for epoch in range(num_epochs):
    model.train()
    train_loss = train(model, train_dataloader, criterion, optimizer, device)
    val_loss, average_score, kappa, f1, auc = evaluate(model, validation_dataloader, device, criterion)
    scheduler.step(val_loss)
    if average_score > best_score:
        best_score = average_score
        torch.save(model.state_dict(), model_checkpoint_name)
        print(f"Score increased to {average_score:.4f}. Model saved!")
    print(f"  validation losss: {val_loss:.4f}")
    print(f"Epoch {epoch + 1}/{num_epochs}")
    print(f"  average score: {average_score:.4f}")
    print(f"  f1: {f1:.4f}")
    print(f"  kappa: {kappa:.4f}")
    print(f"  auc: {auc:.4f}")
