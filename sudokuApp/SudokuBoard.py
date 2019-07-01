# -*- coding: utf-8 -*-
"""
Created on Sat Mar  9 18:48:34 2019

@author: josep
"""
import numpy as np

class SudokuSolver:
    def __init__(self, grid = None):
        if grid is not None:  # if a sudoku grid is passed in check shape/min/max before saving
            if grid.shape != (9,9):
                raise Exception('Grid size', grid.shape,'is not a valid sudoku board')
            elif grid.min() < 0 or grid.max() > 9:
                raise Exception('Sudoku grid entries are not vaid: min = {}, max = {}'.format(grid.min(), grid.max()))
            else:
                self.grid = grid
                
        #load possible candidates for each cell in grid
        self.possible = {i: set(range(1,10)) for i in range(0,89) \
                         if (i%10 != 9)}
    def solve(self):
        #eliminate possible candidates from cells in grid that are already filled
        for r, c in zip(range(9), range(9)):
            if self.grid[r,c] > 0:
                self.possible[r*10+c] = set()
        
        filled = 0  #counts the number of grid positions filled
        lastFilled = 0 #holds fill coubnt of last loop to check for progress
        progress = True #stores whether progress was made on previous loop through grid
        count = 0
        while (0 in set(self.grid.flatten())):
            count += 1
            for row in range(9):
                for col in range(9):
                    # for each row and column index, if solution has not been found yet, narrow search
                    if self.grid[row,col] == 0:
                        quadrantRow = row//3
                        quadrantCol = col//3
                        posSet = self.possible[row*10 + col]
                         
                        #eliminate possibilities by searching numbers stored in same row, column, and quadrant
                        usedNums = set(self.grid[row,0:9])  #creates set with nums used in same row
                        usedNums.update(self.grid[0:9,col]) # updates set with nums in same column
                        usedNums.update(self.grid[quadrantRow*3:(quadrantRow*3 + 3), quadrantCol*3:(quadrantCol*3 + 3)].flatten())  #updates set with nums used in same quadrant
                        
                        posSet = posSet.difference(usedNums)
                        self.possible[row*10 + col] = posSet
                        
                        #if only 1 possibility remaining, fill in number
                        if len(posSet) == 1:
                            answer = posSet.pop()
                            self.grid[row,col] = answer
                            filled += 1
                            #print("\tog({},{}) = {}".format(row, col, answer))
                            continue
                        
                        filled += self.hiddenSingle(row, col) #searches for hidden singles and updates grid accordingly
                        
                        if progress == False and filled == lastFilled:
                            pass
                            # implicit candidate elimination methods
                            # only perform these methods if necessary, its expensive
                            if len(posSet) == 2:
                                self.nakedPair(row, col)
                            elif len(posSet) == 3:
                                self.nakedTriple(row,col)
                            self.pointingOrClaimingPair(row, col)
            #print('filled: ', filled)                
            if (filled == lastFilled):
                #if grid has not updated in last loop and progess already = False (backwards solver was used), then break loop
                if progress == False and count > 50:
                    self.printGrid()
                    print('remaining:', 81 - (self.grid > 0).sum())
                    raise Exception('Error. Sudoku board could not be solved')
                else:
                    progress = False
            else:
                progress = True
            lastFilled = filled
        return self.grid
    
    def hiddenSingle(self, row, col):
        # when a cell contains an options for a number than is not available in any other cell within
        # its row, column or quadrant
        quadrantRow = row//3
        quadrantCol = col//3
        posSet = self.possible[row*10 + col]
        
        # check row
        uniqueInRow = posSet.copy()
        # cycle through row cells possibilities and subtract from this cells possibility set
        [uniqueInRow.difference_update(self.possible[row*10 + c]) for c in range(9) if c != col]
        # if this is only cell in quad that can hold a number then update grid
        if len(uniqueInRow) == 1:
            answer = uniqueInRow.pop()
            self.grid[row,col] = answer
            #print("\tr({},{}) = {}".format(row, col, answer))
            return 1 #skip rest of cell checks
        
        # check column
        uniqueInCol = posSet.copy()
        # cycle through column cells possibilities and subtract from this cells possibility set
        [uniqueInCol.difference_update(self.possible[r*10 + col]) for r in range(9) if r != row]
        # if this is only cell in column that can hold a number then update grid
        if len(uniqueInCol) == 1:
            answer = uniqueInCol.pop()
            self.grid[row,col] = answer
            #print("\tc({},{}) = {}".format(row, col, answer))
            return 1 #skip rest of cell checks
        
        #check quadrant
        uniqueInQuad = posSet.copy()
        # cycle through quadrant cell possibilities and subtract from this cells possibility set
        [uniqueInQuad.difference_update(self.possible[r*10 + c]) \
                 for r in range(quadrantRow*3,(quadrantRow*3 + 3)) \
                 for c in range(quadrantCol*3,(quadrantCol*3 + 3)) \
                 if (r != row or c != col)]
        # if this is only cell in quad that can hold a number then update grid
        if len(uniqueInQuad) == 1: 
            answer = uniqueInQuad.pop()
            self.grid[row,col] = answer
            #print("\tq({},{}) = {}".format(row, col, answer))
            return 1   # skip rest of cell checks
        return 0
        
    def nakedPair(self, row, col):
        # when two cells in a row column or a block have the same pair of candidates, all other instances
        # of those candidates within the same row block or column can be eliminated
        posSet = self.possible[row*10 + col]
        quadrantRow = row//3
        quadrantCol = col//3
        
        # cell id's in row, column, and quadrant
        rowCellIds = [r*10 + col for r in range(9) if r!=row and self.possible.get(r*10 + col) is not None]
                        
        colCellIds = [row*10 + c for c in range(9) if c!=col and self.possible.get(row*10 + c) is not None]
        quadCellIds = [r*10 + c for r in range(quadrantRow*3,(quadrantRow*3 + 3)) \
                             for c in range(quadrantCol*3,(quadrantCol*3 + 3)) \
                             if (c != col or r != row) and self.possible.get(r*10 + c) is not None]

        for cellIdx in set(rowCellIds + colCellIds + quadCellIds):
            # if another cell contains the same 2 candidates, eliminate these candidates from all other cells
            if self.possible[cellIdx] == posSet:
                #if found cell is in same row, eliminate candidate set from all other cells in row
                if cellIdx in rowCellIds:
                    for otherIdx in rowCellIds:
                        if otherIdx != cellIdx:
                            self.possible[otherIdx] = self.possible[otherIdx].difference(posSet)
                #if found cell is in same column, eliminate candidate set from all other cells in column
                if cellIdx in colCellIds:
                    for otherIdx in colCellIds:
                        if otherIdx != cellIdx:
                            self.possible[otherIdx] = self.possible[otherIdx].difference(posSet)
                #if found cell is in same quadrant, eliminate candidate set from all other cells in quadrant
                if cellIdx in quadCellIds:
                    for otherIdx in quadCellIds:
                        if otherIdx != cellIdx:
                            self.possible[otherIdx] = self.possible[otherIdx].difference(posSet)
                break
        
        
    def pointingOrClaimingPair(self, row, col):
        # when a candate appears 2 or 3 times within a quadrant and only in a row or column
        # other instances of the candidate within that row or column and outside the quadrant can be eliminated
        posSet = self.possible[row*10 + col]
        quadrantRow = row//3
        quadrantCol = col//3
        
        #runs checks for each candidate for cell passed in
        for num in posSet:
            OnlyInstancesForQuadInRow = True  #set to false if other cells in the same quad and outside the same row have this num as a candidate
            OnlyInstancesForQuadInCol = True
            OnlyInstancesForRowInQuad = True  #set to false if other cells in the same row and outside the same quad have this num as a candidate
            OnlyInstancesForColInQuad = True
            
            #searches cells within row but outside quadrant
            for c in range(9):
                if (quadrantCol * 3 > c or c >= (quadrantCol * 3 + 3)) and self.grid[row,c] == 0:
                    if num in self.possible.get(row*10 + c):
                        OnlyInstancesForRowInQuad = False
            #searches cells within column but outside quadrant
            for r in range(9):
                if (quadrantRow * 3 > r or r >= (quadrantRow * 3 + 3)) and self.grid[r,col] == 0:
                    if num in self.possible[r*10 + col]:
                        OnlyInstancesForColInQuad = False
            #searches cells within quadrant   
            for rQ in range(quadrantRow*3,(quadrantRow*3 + 3)):
                for cQ in range(quadrantCol*3,(quadrantCol*3 + 3)):
                    if self.grid[rQ,cQ] == 0:  #check that cell has candidates/unfilled
                        if num in self.possible[rQ*10 + cQ]:
                            if rQ != row:
                                OnlyInstancesForQuadInRow = False
                            if cQ != col:
                                OnlyInstancesForQuadInCol = False
                                
            #based on the findings above, eliminate candidates of other cells
            if OnlyInstancesForRowInQuad and (not OnlyInstancesForQuadInRow):
                #delete other instances of num candidate within quadrant and outside row
                for rQ in range(quadrantRow*3,(quadrantRow*3 + 3)):
                    for cQ in range(quadrantCol*3,(quadrantCol*3 + 3)):
                        if rQ != row and self.grid[rQ,cQ] == 0:
                            self.possible[rQ*10 + cQ].discard(num)
            elif (not OnlyInstancesForRowInQuad) and OnlyInstancesForQuadInRow:
                #delete other instances of num candidate within row and outside quadrant
                for c in range(9):
                    if (quadrantCol * 3 > c or c >= (quadrantCol * 3 + 3)) and self.grid[row,c] == 0:
                        self.possible[row*10 + c].discard(num)
            
            if OnlyInstancesForColInQuad and (not OnlyInstancesForQuadInCol):
                #delete other instances of num candidate within quadrant and outside column
                for rQ in range(quadrantRow*3,(quadrantRow*3 + 3)):
                    for cQ in range(quadrantCol*3,(quadrantCol*3 + 3)):
                        if cQ != col and self.grid[rQ,cQ] == 0:
                            self.possible[rQ*10 + cQ].discard(num)
            elif (not OnlyInstancesForColInQuad) and OnlyInstancesForQuadInCol:
                #delete other instances of num candidate within column and outside quadrant
                for r in range(9):
                    if (quadrantRow * 3 > r or r >= (quadrantRow * 3 + 3)) and self.grid[r,col] == 0:
                        self.possible[r*10 + col].discard(num)
    
    def nakedTriple(self, row, col):
        #cell passed needs to have exactly 2 or 3 candidates
        posSet = self.possible[row*10+col]
        quadrantRow = row//3
        quadrantCol = col//3
        
        if len(posSet) == 3:
            #check row, column, and quadrant for 3 (2 + this) cells with subset of these 3 candidates
            
            #check row
            cellsWithMatchingSubsets = {row*10+col}
            for c in range(9):
                if c != col and self.grid[row,c] == 0:
                    if self.possible[row*10+c].issubset(posSet):
                        cellsWithMatchingSubsets.add(row*10+c)
            if len(cellsWithMatchingSubsets) == 3:
                # if nakedTriple is found delete all other instances of nums in row
                for c in range(9):
                    if (row*10+c)  not in cellsWithMatchingSubsets and self.grid[row,c] == 0:
                        self.possible[row*10+c].difference_update(posSet)
            
            #check column
            cellsWithMatchingSubsets = {row*10+col}
            for r in range(9):
                if r != row and self.grid[r,col] == 0:
                    if self.possible[r*10+col].issubset(posSet):
                        cellsWithMatchingSubsets.add(r*10+col)
            if len(cellsWithMatchingSubsets) == 3:
                # if nakedTriple is found delete all other instances of nums in column
                for r in range(9):
                    if (r*10+col) not in cellsWithMatchingSubsets and self.grid[r,col] == 0:
                        self.possible[r*10+col].difference_update(posSet)
            
            #check quadrant
            cellsWithMatchingSubsets = {row*10+col}
            for rQ in range(quadrantRow*3,(quadrantRow*3 + 3)):
                    for cQ in range(quadrantCol*3,(quadrantCol*3 + 3)):
                        if rQ != row and cQ != col and self.grid[rQ,cQ] == 0:
                            if self.possible[rQ*10+cQ].issubset(posSet):
                                cellsWithMatchingSubsets.add(rQ*10+cQ)
            if len(cellsWithMatchingSubsets) == 3:
                # if nakedTriple is found delete all other instances of nums in quadrant
                for rQ in range(quadrantRow*3,(quadrantRow*3 + 3)):
                    for cQ in range(quadrantCol*3,(quadrantCol*3 + 3)):
                        if (rQ*10+cQ) not in cellsWithMatchingSubsets and self.grid[rQ,cQ] == 0:
                            self.possible[rQ*10+cQ].difference_update(posSet)
        elif len(posSet) == 2:
            pass
            #check row, column, and quadrant
        else:
            raise Exception('Error. cell with incorrect number of candidates passed to nakedTriple method')
        
    def getGrid(self):
        return self.grid
    
    def setGrid(self,grid):
        self.grid = grid
        
    def printGrid(self):
        #if grid has been solved
        if (self.grid > 0).sum() == 81:
            for r in range(9):
                print('\n|', end = '')
                for c in range(9):
                    print(str(self.grid[r,c])+'|',end = '')
             
        else:
            for r in range(9):
                print('\n|', end = '')
                for c in range(9):
                    if self.grid[r,c] > 0:
                        print('{:4}{:2}{:4}|'.format('',str(self.grid[r,c]),''),end = '')
                    else:
                        print('{:10}|'.format(str(self.possible[r*10+c])),end = '')
        print()
    def getPossible(self):
        return self.possible
    
    def loadBoardEasy(self):
        grid = np.zeros((9,9), dtype=np.int)
        
        grid[0,1] = 7
        grid[0,2] = 6
        grid[0,3] = 1
        grid[0,4] = 4
        grid[0,8] = 2
        
        grid[1,3] = 8
        grid[1,4] = 6
        grid[1,6] = 9
        
        grid[2,2] = 4
        grid[2,3] = 2
        grid[2,4] = 5
        grid[2,7] = 3
        
        grid[3,1] = 5
        grid[3,5] = 1
        grid[3,8] = 8
        
        grid[4,1] = 3
        grid[4,2] = 7
        grid[4,3] = 5
        grid[4,5] = 8
        grid[4,6] = 4
        grid[4,7] = 2
        
        grid[5,0] = 1
        grid[5,3] = 3
        grid[5,7] = 7
        
        grid[6,1] = 6
        grid[6,4] = 8
        grid[6,5] = 4
        grid[6,6] = 2
        
        grid[7,2] = 2
        grid[7,4] = 1
        grid[7,5] = 5
        
        grid[8,0] = 9
        grid[8,4] = 3
        grid[8,5] = 2
        grid[8,6] = 7
        grid[8,7] = 8
        
        self.grid = grid
    
    def loadBoardHard(self):
        #https://www.websudoku.com/?level=3&set_id=9543140687
        grid = np.zeros((9,9), dtype=np.int)
        
        grid[0,3] = 6
        grid[0,4] = 1
        grid[0,6] = 9
        grid[0,8] = 7
        
        grid[1,2] = 1
        grid[1,6] = 5
        grid[1,7] = 2
        
        grid[2,0] = 9
        grid[2,1] = 2
        
        grid[3,1] = 8
        grid[3,2] = 9
        grid[3,6] = 6
        grid[3,8] = 2

        grid[4,4] = 5
        
        grid[5,0] = 2
        grid[5,2] = 4
        grid[5,6] = 8
        grid[5,7] = 5
        
        grid[6,7] = 7
        grid[6,8] = 5
        
        grid[7,1] = 4
        grid[7,2] = 5
        grid[7,6] = 3
        
        grid[8,0] = 1
        grid[8,2] = 8
        grid[8,4] = 7
        grid[8,5] = 3
        
        self.grid = grid
    
    def loadBoardEvil(self):
        #https://www.websudoku.com/?level=4&set_id=7356228424
        grid = np.zeros((9,9), dtype=np.int)
        
        grid[0,0] = 2
        grid[0,3] = 8
        grid[0,6] = 6
        
        grid[1,0] = 6
        grid[1,8] = 8
        
        grid[2,5] = 5
        grid[2,6] = 2
        grid[2,7] = 9
        
        grid[3,1] = 4
        grid[3,4] = 5
        grid[3,5] = 3
        
        grid[4,1] = 5
        grid[4,4] = 8
        grid[4,7] = 4
        
        grid[5,3] = 1
        grid[5,4] = 7
        grid[5,7] = 6
        
        grid[6,1] = 3
        grid[6,2] = 1
        grid[6,3] = 5
        
        grid[7,0] = 9
        grid[7,8] = 2
        
        grid[8,2] = 8
        grid[8,5] = 1
        grid[8,8] = 7
        
        self.grid = grid
    
    def loadWorldsHardest(self):
        #https://www.websudoku.com/?level=4&set_id=7356228424
        grid = np.zeros((9,9), dtype=np.int)
        
        grid[0,0] = 8
        
        grid[1,2] = 3
        grid[1,3] = 6
        
        grid[2,1] = 7
        grid[2,4] = 9
        grid[2,6] = 2
        
        grid[3,1] = 5
        grid[3,5] = 7
        
        grid[4,4] = 4
        grid[4,5] = 5
        grid[4,6] = 7
        
        grid[5,3] = 1
        grid[5,7] = 3
        
        grid[6,2] = 1
        grid[6,7] = 6
        grid[6,8] = 8
        
        grid[7,2] = 8
        grid[7,3] = 5
        grid[7,7] = 1
        
        grid[8,1] = 9
        grid[8,6] = 4
        
        self.grid = grid
if __name__ == '__main__':
    solver = SudokuSolver()
    solver.loadBoardEvil()
    solution = solver.solve()
    solver.printGrid()
    
    