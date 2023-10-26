This repository is about ODIR 2019, a multi-label eye disease classification challenge. 

This work focusses on the RETFound retinal disease foundational model. More specifically, we test the claim that the RETFound model can easily be adapted to custom tasks. We compare it to the following baseline models on the test set of the ODIR2019 challenge: ResNet50, ViT-16 vision transformer and EfficientNet (B3). The default set up for all models is that we concatenate the features of the images after putting it through the models to let a classifier predict the diseases of a patient. In addition, we implemented a MIL-head in plug-and-play manner on top of the foundational model. However, we did not find improvements over the baseline models. Therefore, we also tested finetuning the RETFound model on single-eye classification. All models (and different configurations) can be found in the models folder in src. 

The retinal images can be downloaded from the Grand challenge website https://odir2019.grand-challenge.org/dataset/. We applied field of view cropping to remove the background surrounding the retinal images. The code is supplied in src/cropping.py. We recommend doing this once before training since it takes around 20 minutes per dataset.
