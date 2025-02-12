import torch
import numpy as np
from segment_anything import sam_model_registry, SamPredictor
from pathlib import Path
import cv2
import json
from tqdm import tqdm

class ImageEmbeddingGenerator:
    def __init__(self, checkpoint_path, model_type="vit_h"):
        """
        Initialize the SAM model for generating image embeddings
        
        Args:
            checkpoint_path: Path to the SAM model checkpoint
            model_type: Type of SAM model (vit_h, vit_l, vit_b)
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.sam = sam_model_registry[model_type](checkpoint=checkpoint_path)
        self.sam.to(device=self.device)
        self.predictor = SamPredictor(self.sam)
        
    def generate_embedding(self, image_path):
        """
        Generate embedding for a single image
        
        Args:
            image_path: Path to the input image
            
        Returns:
            embedding: Image embedding tensor
            image_size: Original image size
        """
        image = cv2.imread(str(image_path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Generate embedding
        self.predictor.set_image(image)
        embedding = self.predictor.get_image_embedding().cpu().numpy()
        
        return embedding, image.shape[:2]
    
    def process_directory(self, input_dir, output_dir):
        """
        Process all images in a directory and save their embeddings
        
        Args:
            input_dir: Directory containing input images
            output_dir: Directory to save embeddings
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        image_files = list(input_path.glob("*.jpg")) + list(input_path.glob("*.png"))
        
        for image_file in tqdm(image_files, desc="Generating embeddings"):
            # Generate embedding
            embedding, image_size = self.generate_embedding(image_file)
            
            # Save embedding and metadata
            output_name = output_path / f"{image_file.stem}_embedding"
            np.save(f"{output_name}.npy", embedding)
            
            metadata = {
                "image_size": image_size,
                "original_image": str(image_file),
                "embedding_shape": embedding.shape
            }
            
            with open(f"{output_name}.json", 'w') as f:
                json.dump(metadata, f)

def main():
    # Update these paths according to your setup
    CHECKPOINT_PATH = "sam-model/sam_vit_h_4b8939.pth"
    INPUT_DIR = "data/input_images"
    OUTPUT_DIR = "data/embeddings"
    
    generator = ImageEmbeddingGenerator(CHECKPOINT_PATH)
    generator.process_directory(INPUT_DIR, OUTPUT_DIR)

if __name__ == "__main__":
    main() 