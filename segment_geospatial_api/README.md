## Cleanup  

To clean up temporary files and downloaded models:

```bash
python scripts/cleanup.py
```
## Install 
install env
```bash
conda create -n geo python
conda activate geo
conda install -c conda-forge mamba
mamba install -c conda-forge gdal
mamba install -c conda-forge segment-geospatial
mamba install -c conda-forge groundingdino-py segment-anything-fast
mamba install -c conda-forge pydantic fastapi uvicorn loguru
mamba install -c conda-forge pydantic-settings
```
use GPU
```bash
mamba install -c conda-forge segment-geospatial "pytorch=*=cuda*"
```

use GeoAI
```bash
pip install "geoai-py[all]"
```



