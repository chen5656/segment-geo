# LightHouse - Lightweight House Detection Web Tool

A pure frontend lightweight building detection tool that supports quick identification and editing of building outlines.

## Features
- 🏠 Focused on building detection
- 🚀 Pure frontend implementation, no backend required
- ⚡ Lightweight model, fast response
- ✏️ Interactive editing capabilities
- 🗺️ Geospatial data support

## Technical Stack
- TensorFlow.js
- React
- Mapbox GL JS

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 14+
- SAM model checkpoint (will be downloaded automatically)

### Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd LightHouse
```

2. Set up Python environment:
```bash
conda env create -f environment.yml
conda activate lighthouse
```

3. Initialize project (this will download required models and sample data):
```bash
python scripts/initialize.py
```

### Usage Options

#### Option 1: Using Sample Data
1. Run the demo with provided sample images:
```bash
python scripts/image_encoder.py --use-samples
```

#### Option 2: Using Custom Images
1. Place your satellite/aerial images in `data/input_images`
2. Run the image encoder script:
```bash
python scripts/image_encoder.py --input-dir data/input_images
```

The embeddings will be saved in `data/embeddings` in both cases.

## Project Structure
```
LightHouse/
├── sam-model/          # SAM model checkpoint
├── data/
│   ├── input_images/   # Source images
│   └── embeddings/     # Generated embeddings
├── scripts/
│   └── image_encoder.py # Embedding generation script
└── web/                # Frontend application
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

### Segment Anything Model

This project builds upon the Segment Anything Model (SAM). If you use this project in your research, please cite:
```bibtex
@article{kirillov2023segany,
  title={Segment Anything},
  author={Kirillov, Alexander and Mintun, Eric and Ravi, Nikhila and Mao, Hanzi and Rolland, Chloe and Gustafson, Laura and Xiao, Tete and Whitehead, Spencer and Berg, Alexander C. and Lo, Wan-Yen and Doll{\'a}r, Piotr and Girshick, Ross},
  journal={arXiv:2304.02643},
  year={2023}
}
```

### Segment Geospatial Package

This project uses the samgeo package. If you use this project, please also cite:
```bibtex
@article{wu2023samgeo,
  title={samgeo: A Python package for segmenting geospatial data with the Segment Anything Model (SAM)},
  author={Wu, Q. and Osco, L.},
  journal={Journal of Open Source Software},
  volume={8},
  number={89},
  pages={5663},
  year={2023},
  doi={10.21105/joss.05663}
}

@article{osco2023segment,
  title={The Segment Anything Model (SAM) for remote sensing applications: From zero to one shot},
  author={Osco, L. P. and Wu, Q. and de Lemos, E. L. and Gonçalves, W. N. and Ramos, A. P. M. and Li, J. and Junior, J. M.},
  journal={International Journal of Applied Earth Observation and Geoinformation},
  volume={124},
  pages={103540},
  year={2023},
  doi={10.1016/j.jag.2023.103540}
}
```
