import os
import requests
from pathlib import Path
import gdown
import shutil
from tqdm import tqdm

class ProjectInitializer:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.sam_model_dir = self.root_dir / "sam-model"
        self.sample_data_dir = self.root_dir / "data" / "samples"
        self.model_url = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth"
        self.samples_url = "https://drive.google.com/uc?id=YOUR_GDRIVE_ID"  # We'll add sample images URL

    def download_file(self, url, dest_path):
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(dest_path, 'wb') as file, tqdm(
            desc=dest_path.name,
            total=total_size,
            unit='iB',
            unit_scale=True
        ) as pbar:
            for data in response.iter_content(chunk_size=1024):
                size = file.write(data)
                pbar.update(size)

    def setup_directories(self):
        """Create necessary directories"""
        dirs = [
            self.sam_model_dir,
            self.sample_data_dir,
            self.root_dir / "data" / "input_images",
            self.root_dir / "data" / "embeddings"
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    def download_sam_model(self):
        """Download SAM model if not exists"""
        model_path = self.sam_model_dir / "sam_vit_h_4b8939.pth"
        if not model_path.exists():
            print("Downloading SAM model...")
            self.download_file(self.model_url, model_path)

    def download_sample_data(self):
        """Download sample satellite images"""
        if not list(self.sample_data_dir.glob("*.jpg")):
            print("Downloading sample images...")
            # We'll add sample data download logic here
            pass

    def initialize(self):
        """Run full initialization"""
        print("Initializing LightHouse project...")
        self.setup_directories()
        self.download_sam_model()
        self.download_sample_data()
        print("Initialization complete!")

if __name__ == "__main__":
    initializer = ProjectInitializer()
    initializer.initialize() 