import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import numpy as np
import scipy
import os

import matplotlib.pyplot as plt
import pandas as pd


directoryPath = "";


class App(QWidget):
 
    def __init__(self):
        super().__init__()
        self.title = 'PyQt5 button - pythonspot.com'
        self.left = 10
        self.top = 10
        self.width = 550
        self.height = 500
        self.numberOfLevelsToScan = 0;
        self.values = pd.DataFrame(columns = ['File','Energy','Diff Energy']);
        self.initUI()
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.createGridLayout();
        self.createOutputGrid();
        self.show()
    
    def createGridLayout(self):
        self.groupBox = QGroupBox('Choosing Directory',self);
        self.groupBox.setMinimumWidth(500);
        #self.groupBox.setGeometry(10,10,10,10)
        layout = QGridLayout();
        layout.setColumnStretch(1,4);
        layout.setColumnStretch(2,4);

        self.directoryChooserBtn = QPushButton("Choose Directory",self);
        self.directoryChooserBtn.clicked.connect(self.buttonControl);
        self.levelSelector = QCheckBox("Only scan the first directory", self);self.levelSelector.toggle();self.levelSelector.stateChanged.connect(self.levelChanger);

        self.dpLabel = QLabel("Directory Path",self);
        self.directoryPathLabel = QLabel("Path",self);

        
        layout.addWidget(self.directoryChooserBtn,0,0);
        layout.addWidget(self.levelSelector,0,2);
        layout.addWidget(self.dpLabel,1,0);
        layout.addWidget(self.directoryPathLabel,1,1);
        self.groupBox.setLayout(layout);

    def createOutputGrid(self):  #making second grid for showing output
        self.outputBox = QGroupBox("Output",self);
        self.outputBox.setGeometry(0,75,500,400)
        
        layout = QGridLayout();
        layout.setColumnStretch(1,4);
        layout.setColumnStretch(2,4);

        self.outputText = QLabel("Please Choose A Directory");

        self.outputTable = QTableWidget(1,3);
        self.outputTable.setHorizontalHeaderLabels(str("Name;Total Energy(eV); Diff Total Energy").split(";"))
        self.outputTable.setMinimumWidth(480);   

        self.plotBtn = QPushButton("Plot The Values");self.plotBtn.clicked.connect(self.plotEvent);

        self.saveBtn = QPushButton("Save values"); self.saveBtn.clicked.connect(self.saveEvent);
        layout.addWidget(self.outputText,0,0);
        layout.addWidget(self.outputTable,1,0);
        layout.addWidget(self.plotBtn,0,1);
        layout.addWidget(self.saveBtn,0,2);
        self.outputBox.setLayout(layout);


    ############################Define the event handlers
    def buttonControl(self):
        file = str(QFileDialog.getExistingDirectory(self, "Select Directory"));
        self.directoryPathLabel.setText(file);
        self.fileLister(file);
    def levelChanger(self,state):
        if state == 2:
            self.numberOfLevelsToScan=0;
            print(True);
        else: 
            self.numberOfLevelsToScan = 10;
            print(False);
    def plotEvent(self):
       # values = np.ndarray(self.directory, self.Energy, self.diffEnergy);
        indexesColumns = self.outputTable.selectionModel().selectedColumns();
        if (len(indexesColumns) ==2):
            xIndex = indexesColumns[0].column();
            yIndex = indexesColumns[1].column();
            self.plotting(xIndex, yIndex);
        else:
            self.outputText.setText("Not enough columns are selected, using first columns")
            message = QMessageBox(QMessageBox.Information,"Default Values","Default Values");
            ret = message.exec_()
            self.plotting(0,1);
    def saveEvent(self):
        print("save");
        file,_ = QFileDialog.getSaveFileName(self, "Select File To save");
        if file:
            with open(file,'w') as f:
                self.values.to_csv(file)
        
    ##################################################Define the Methods
    def fileLister(self, directoryName):
        self.fileNames = list()
        self.paths = list();
        #Energy = list()
        self.Energy = np.empty(0,dtype = np.float64);
        self.directory = list()
        for root, dirs, files in os.walk(directoryName):
            if root[len(directoryName)+1:].count(os.sep)<=self.numberOfLevelsToScan:
                for file in files:
                    if file.endswith("OUTCAR"):
                        self.directory.append(root.replace(str(directoryName),"").replace(str(os.sep),"",1)); #appending only dir name
                        self.paths.append(root.replace(".//","").replace("\\","/"))  #appending he full path
                        self.Energy = np.append(self.Energy,[float(self.energyFinder(os.path.join(root,file)))])  #appending the Total Energy
        if (len(self.Energy)>0):
            minEnergy = np.min(self.Energy);
            print (self.Energy, minEnergy);
            self.diffEnergy = self.Energy - minEnergy;
            print(self.diffEnergy);
            d = {'File':self.directory, 'Energy':self.Energy, 'Diff Energy':self.diffEnergy};
            self.values = pd.DataFrame(d);
            self.values['File'] = self.values['File'].astype('category');
            self.updatingTable(clearing = False);
        else:
            d = {'File':[], 'Energy':[], 'Diff Energy':[]};
            self.values = pd.DataFrame(d);
            self.updatingTable(clearing=True);
            self.outputText.setText("No OUTCAR file found");
    def energyFinder(self, file):
        E = 0
        for line in open(file):
            if "  free  energy   TOTEN  = " in line:
                words= line.split()
                E = words[4]
        return E
    def updatingTable(self, clearing=False):
        self.clearingTable(self.outputTable);
        if clearing ==False:
            for i,dir in enumerate(self.directory):
                self.outputTable.insertRow(i);
                self.outputTable.setItem(i,0,QTableWidgetItem(dir));
                print(self.Energy[i]);
                self.outputTable.setItem(i,1,QTableWidgetItem(str(self.Energy[i])));
                self.outputTable.setItem(i,2,QTableWidgetItem(str(self.diffEnergy[i])));
        else:
            # while (self.outputTable.rowCount() > 0):
            #     self.outputTable.removeRow(0);
            self.clearingTable(self.outputTable);
    def clearingTable(self, table):
        while (table.rowCount() > 0):
            table.removeRow(0);
    def plotting(self, xIndex,yIndex,title=""):
        plt.close();
        x = self.values[self.values.columns[xIndex]].cat.codes;
        y = self.values[self.values.columns[yIndex]];
        
        #smoothing
        from scipy.interpolate import  CubicSpline
        bci = CubicSpline(x, y, extrapolate=False)
        xNew = np.linspace(min(x),max(x),1000)
        yNew = bci(xNew)

        plt.scatter(x,y,linewidth = 3, marker = '^')
        plt.plot(xNew,yNew,'r', linewidth = 1, alpha = 0.5);
        columnNames = self.values.columns;
        plt.xlabel(columnNames[xIndex]);
        plt.ylabel (columnNames[yIndex]);

        plt.grid(True);
        plt.show();
            


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
