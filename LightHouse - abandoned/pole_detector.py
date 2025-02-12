import torch
import torchvision
import numpy as np
from segment_anything import SamAutomaticMaskGenerator, sam_model_registry
from torch.utils.data import DataLoader, Dataset
import os
import cv2
from tqdm import tqdm
from torchvision import transforms

# 配置参数
MODEL_PATH = "model/sam2.1_hiera_large.pt"  # 原始SAM模型路径
OUTPUT_DIR = "output_models/"  # 输出模型存储路径
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
TARGET_CLASS = "pole"  # 固定目标为杆状物

class PoleDataset(Dataset):
    """专门用于杆状物数据的数据集类"""
    def __init__(self, data_path, is_train=True):
        self.data_path = data_path
        self.samples = []
        
        # 加载正样本（杆状物图片）
        positive_path = os.path.join(data_path, "positive")
        for img_name in os.listdir(positive_path):
            if img_name.endswith(('.jpg', '.png', '.jpeg')):
                self.samples.append({
                    'path': os.path.join(positive_path, img_name),
                    'label': 1
                })
        
        # 加载负样本（非杆状物图片）
        negative_path = os.path.join(data_path, "negative")
        for img_name in os.listdir(negative_path):
            if img_name.endswith(('.jpg', '.png', '.jpeg')):
                self.samples.append({
                    'path': os.path.join(negative_path, img_name),
                    'label': 0
                })
        
        # 添加数据增强
        if is_train:
            self.transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.RandomHorizontalFlip(),
                transforms.RandomRotation(10),
                transforms.ColorJitter(brightness=0.2, contrast=0.2),
                transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                  std=[0.229, 0.224, 0.225])
            ])
        else:
            self.transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                  std=[0.229, 0.224, 0.225])
            ])
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        sample = self.samples[idx]
        image = cv2.imread(sample['path'])
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 应用数据增强
        image = self.transform(image)
        label = torch.tensor(sample['label'], dtype=torch.long)
        
        return image, label

def create_pole_detector():
    """
    自动生成专门用于检测杆状物的轻量化模型
    :return: 轻量化模型的路径
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Step 1: 加载SAM模型
    print("Loading SAM model...")
    sam_model = sam_model_registry["vit_h"](checkpoint=MODEL_PATH)
    sam_model.to(DEVICE)

    # Step 2: 准备数据
    print("Preparing pole detection data...")
    data_path = "data/poles/"  # 杆状物数据集路径
    dataset = PoleDataset(data_path=data_path)
    dataloader = DataLoader(dataset, batch_size=8, shuffle=True)

    # Step 3: 定义知识蒸馏损失
    def distillation_loss(teacher_outputs, student_outputs, temperature=2.0):
        soft_targets = torch.nn.functional.softmax(teacher_outputs / temperature, dim=1)
        student_log_softmax = torch.nn.functional.log_softmax(student_outputs / temperature, dim=1)
        return torch.nn.functional.kl_div(student_log_softmax, soft_targets, reduction='batchmean')

    # Step 4: 创建轻量化模型架构
    class LightPoleDetector(torch.nn.Module):
        def __init__(self):
            super().__init__()
            # 使用轻量级backbone
            self.backbone = torchvision.models.mobilenet_v3_small(pretrained=True)
            # 修改最后的分类层
            self.backbone.classifier[-1] = torch.nn.Linear(576, 2)  # 二分类：是否为杆状物
            
        def forward(self, x):
            return self.backbone(x)

    # 初始化轻量化模型
    light_model = LightPoleDetector().to(DEVICE)
    
    # Step 5: 训练和蒸馏
    print("Starting knowledge distillation...")
    optimizer = torch.optim.AdamW(light_model.parameters(), lr=1e-4)
    num_epochs = 50
    
    for epoch in range(num_epochs):
        light_model.train()
        total_loss = 0
        progress_bar = tqdm(dataloader, desc=f'Epoch {epoch+1}/{num_epochs}')
        
        for batch_images, batch_labels in progress_bar:
            batch_images = batch_images.to(DEVICE)
            batch_labels = batch_labels.to(DEVICE)
            
            # 获取教师模型（SAM）的输出
            with torch.no_grad():
                teacher_outputs = sam_model(batch_images)
            
            # 获取学生模型的输出
            student_outputs = light_model(batch_images)
            
            # 计算蒸馏损失
            loss = distillation_loss(teacher_outputs, student_outputs)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            progress_bar.set_postfix({'loss': total_loss/(progress_bar.n+1)})

    # Step 6: 保存轻量化模型
    output_path = os.path.join(OUTPUT_DIR, "pole_detector_small.pth")
    torch.save({
        'model_state_dict': light_model.state_dict(),
        'config': {
            'input_size': (224, 224),
            'target_class': TARGET_CLASS
        }
    }, output_path)
    
    print(f"Lightweight pole detector saved at: {output_path}")
    return output_path

def detect_poles(image_path, model_path):
    """
    使用轻量化模型检测图片中的杆状物
    :param image_path: 输入图片路径
    :param model_path: 模型路径
    :return: 检测结果
    """
    # 加载模型
    model = LightPoleDetector()
    checkpoint = torch.load(model_path)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(DEVICE)
    model.eval()
    
    # 处理图片
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = cv2.resize(image, (224, 224))
    image_tensor = torch.from_numpy(image).float().permute(2, 0, 1).unsqueeze(0) / 255.0
    
    # 预测
    with torch.no_grad():
        output = model(image_tensor.to(DEVICE))
        prediction = torch.softmax(output, dim=1)
        is_pole = prediction[0][1].item() > 0.5
        
    return is_pole, prediction[0][1].item()

if __name__ == "__main__":
    # 自动执行模型生成
    try:
        output_model_path = create_pole_detector()
        print(f"Successfully created pole detector model at: {output_model_path}")
        
        # 测试模型
        test_image = "test_images/test_pole.jpg"
        if os.path.exists(test_image):
            is_pole, confidence = detect_poles(test_image, output_model_path)
            print(f"Test result - Is pole: {is_pole}, Confidence: {confidence:.2f}")
            
    except Exception as e:
        print(f"An error occurred: {e}") 