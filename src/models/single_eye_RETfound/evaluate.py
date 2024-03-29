import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
from torchvision import transforms, models
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import os

from torchvision import datasets
from tqdm.notebook import tqdm
import numpy as np
import csv


from sklearn.model_selection import train_test_split
from sklearn import metrics


#calculate kappa, F-1 socre and AUC value
def ODIR_Metrics(gt_data, pr_data):
    """ function from ODIR2019 challenge """
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
            all_logits.append(logits.cpu().numpy())

    all_labels = np.vstack(all_labels)
    all_logits = np.vstack(all_logits)

    all_preds = (all_logits > 0.5).astype(np.float32)
    # val_loss, average_score, kappa, f1, auc, val_confusion, val_accuracy
    kappa, f1, auc, final_score = ODIR_Metrics(all_labels, all_preds)

    return val_loss / len(dataloader), final_score, kappa, f1, auc