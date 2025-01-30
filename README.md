Clone this repository to your computer

# make a copy of .env_example and rename it to .env, and update its value.

# run with docker
## right click on file docker-compose.dev.yml and select "Compose Up"

# run without docker

## First time user
### run npm install for frontend
```
cd segment_geospatial_frontend
npm install
```
### create conda environment with environment.yml and activate it
```
cd segment_geospatial_api
conda env create -f environment.yml
conda activate geo_env
```

## start api and frontend
Open a new terminal and run the following commands:
```
cd segment_geospatial_api
python -m app.main
```
```
cd segment_geospatial_frontend
npm run start
```

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
