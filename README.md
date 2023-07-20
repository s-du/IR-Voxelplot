<p align="center">
    <a href="https://ibb.co/2ZPY1zW"><img src="https://i.ibb.co/dm6JwNj/Voxel-Plot3.png" alt="Voxel-Plot3" border="0"></a>
</p>

## Introduction
IR-Voxelplot is a simple Open3d-based application for visualizing thermal images (from drones) as 3d plots. It uses a 'voxel' representation, created from the input data. Some simple filtering algorithm are also implemented. 

**The project is still in pre-release, so do not hesitate to send your recommendations or the bugs you encountered!**

<p align="center">
    <a href="https://ibb.co/Zzg7HkM"><img src="https://i.ibb.co/23MH8fk/Voxel-gui.png" alt="Voxel-gui" border="0"></a>
    
    GUI for plotting thermal images as 'voxel' maps
</p>


## Principle
The application allows to process DJI thermal drone pictures (DJI Mavic 2 Enterprised Advanced and DJI Mavic 3 Thermal).
It reads the embedded raw temperature data and converts it into a point cloud (x and y coordinates correspond to the pixel location and the z coordinate is the measured temperature).
Then, the point cloud is converted into a voxel grid, using Open3D library. 

### Step 1: Importing an image
Simply choose an infrared thermal image as coming out of the drone

### Step 2: Play with the view controls
Choose some lighting options and define a temperature range! More options to come!

<p align="center">
    <a href="https://ibb.co/1r35B0M"><img src="https://i.ibb.co/2vwQRFS/Voxel-Plot2.png" alt="Voxel-Plot2" border="0"></a>
    
    Playing with voxels size
</p>

## Installation instructions

1. Clone the repository:
```
git clone https://github.com/s-du/IR-Voxelplot
```

2. Navigate to the app directory:
```
cd IR-Voxelplot
```

3. Install the required dependencies:
```
pip install -r requirements.txt
```

4. Run the app:
```
python main.py
```

## Contributing

Contributions to the IRMapper App are welcome! If you find any bugs, have suggestions for new features, or would like to contribute enhancements, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make the necessary changes and commit them.
4. Push your changes to your fork.
5. Submit a pull request describing your changes.


