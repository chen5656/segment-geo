
These instructions assume that you already have Docker and Docker-compose installed on your machine - if not, please follow the instructions here.

Clone this repository to your computer
Navigate to the root of the project: cd car-evaluation-project
Build the docker images using docker-compose up -d --build
This may take a minute
Open your browser and navigate to http://localhost:8501 to use the application.

# Citations

## Segment Anything Model

This project builds upon the Segment Anything Model (SAM). If you use this project in your research, please cite:
@article{kirillov2023segany,
  title={Segment Anything},
  author={Kirillov, Alexander and Mintun, Eric and Ravi, Nikhila and Mao, Hanzi and Rolland, Chloe and Gustafson, Laura and Xiao, Tete and Whitehead, Spencer and Berg, Alexander C. and Lo, Wan-Yen and Doll{\'a}r, Piotr and Girshick, Ross},
  journal={arXiv:2304.02643},
  year={2023}
}
