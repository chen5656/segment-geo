Clone this repository to your computer
# run npm install for frontend
cd segment_geospatial_frontend
npm install
#create conda environment with environment.yml
conda env create -f environment.yml
# activate conda environment
conda activate geo_env
# start api
cd segment_geospatial_api
python -m app.main
# start frontend
cd segment_geospatial_frontend
npm run start

# Citations

## segment-geospatial module

## Segment Anything Model

This project builds upon the Segment Anything Model (SAM). If you use this project in your research, please cite:
@article{kirillov2023segany,
  title={Segment Anything},
  author={Kirillov, Alexander and Mintun, Eric and Ravi, Nikhila and Mao, Hanzi and Rolland, Chloe and Gustafson, Laura and Xiao, Tete and Whitehead, Spencer and Berg, Alexander C. and Lo, Wan-Yen and Doll{\'a}r, Piotr and Girshick, Ross},
  journal={arXiv:2304.02643},
  year={2023}
}
