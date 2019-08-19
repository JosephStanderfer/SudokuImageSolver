# SudokuImageSolver
The Sudoku Image Solver is a Flask web app that uses image processing (blob, line, and corner detection), a convolution neural net, and candidate elimination algorithms to interpret and solve a sudoku puzzle passed to it as a picture.

The app is currently deployed on google app engine. Link: http://sudoku-image-solver.appspot.com/

## Requirements
	- Run using Python 3.6 or 3.7
	- See "requirements.txt" for a list of packages to install

## Getting started
	1. Open a terminal or Anaconda Prompt and navigate to the downloaded project directory
	2. Type and enter "pip install -r requirements.txt" to install the required packages
	3. Enter "python main.py" to run the application
	4. Wait a few seconds then type "http://localhost:5000/" in your web browser and the application will appear.



# Implementation Details
## Image Processing
There were dozens of methods required to process the images and extract the digit grids. An abbreviated summary is given below:

1. Cleaned image using an edge detection kernel and OpenCV’s Kernel Adaptive Threshold
2. Located the puzzle grid by iterating through the image pixels and using OpenCV’s floodFill function. I judged the puzzle to be the “blob” the highest squared area in the picture
3. Straightened the puzzle within the image using OpenCV’s HoughLines on the grid
4. Stretched the grid to the edges using OpenCV’s getPerspectiveTransform function. The 4 corners parameters were found using OpenCV’s cornerHarris function while filtering for the outermost.
5. Removed the grid lines by setting the locations of the grid mask, found during the floodfill step, to the 10th percentile of the image color values
6. Divided the image into 81 cells (9X9) then used OpenCV’s flood fill again to find the digit within each cell
7. Created digit images by again iterating through pixels with OpenCV’s flood fill function and setting several thresholds (bounding size, length, width, coordinates, etc…) for separating digits from noise
8. Centered the digit images within the cell by finding its bounding box and rolling pixels across the cell until it was in the middle
9. Predicted the digit values using a CNN from Kera’s Tensorflow. The training was a combination of the MNIST dataset and 3000+ self-made examples. The MNIST data was useful, even though it was handwritten digits, because it provided a degree of translational learning and therefore better accuracy

## Solving
The Sudoku puzzles are solved through the process of elimination. Each cell has a set of 9 possible values (ie. candidates). The program loops through each one of the cells and eliminates candidates using a variety of methods extrapolated from Sudoku's basic rules. Names and descriptions of these candidate elimination algorithms are shown below. The solution for each cell is found when there is only 1 remaining candidate. The program continues looping through the puzzle and applying the algorithms until all cells are filled.
- Naked Single: When a cell has only 1 remaining candidate, that digit is the cells solution
- Hidden Single: When a cell contains a candidate number than is not available for any other cell within its row, column, or block, then that number is the cell's solution
- Naked Pair: When two cells in a row column or a block have the same pair of remaining candidates (Ex:[2,4] [2,4]), all other instances of those candidates within the same row, block, or column can be eliminated
- Hidden Pair: When 2 cells with the same row, column, or block each have and are the only cells that have 2 specific candidates (Ex:[1,2,4] [1,2,5]), then all other candidates can be eliminated for those 3 cells
- Pointing Pair: When a candate appears 2 or 3 times within a block and only in a single row or column, all other instances of the candidate within that row or column, and outside the quadrant, can be eliminated
- Naked Triple: When 3 cells in a row, column, or quadrant share the same set of 3 remaining candidates between them (Ex:[1,2] [2,3] [3,2]), then all other instances of those 3 candidates can be eliminated from the row, column, or block

