from SimulationEngine.ClassicDEVS.DEVSCoupledModel import DEVSCoupledModel

from Data.GlobalVar import GlobalVar
from Models.ControlSystem.DspPpManager import DspPpManager
from Models.ControlSystem.ScheduleManager import ScheduleManager
from Models.ExperimentalFrame.Analyzer import Analyzer
from Models.ExperimentalFrame.Generator import Generator
from Models.PhysicalSystem.CustomerQueue import CustomerQueue
from Models.PhysicalSystem.Shuttle import Shuttle
# from Visualizer.Visualizer import Visualizer
from datetime import datetime


class MobilitySim_model(DEVSCoupledModel):

    def __init__(self, objConfiguration, jsonPath, iter, maxSim, prevAnalysisModel, renderTime, numShuttle, maxShuttle, isShuttleChange, genEndTime, EDServiceRate, psgrPercent, simulationMode):
        super().__init__("MobilitySim_model")                 
        self.objConfiguration = objConfiguration
        self.iter = iter
        self.maxSim = maxSim
        self.numShuttle = numShuttle
        self.maxShuttle = maxShuttle
        self.isShuttleChange = isShuttleChange
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        self.scenarioID = f"{current_time}_{maxSim}_{psgrPercent}_{iter}"

        ## map.json ##
        graph_data = objConfiguration.getConfiguration("graph_data")
        node_data = objConfiguration.getConfiguration("node_data")

        ## shuttleInfo.json ##
        shuttleInfo = objConfiguration.getConfiguration("shuttleInfo")
        
        
        ## passengerInfo.json ##
        validGridList = objConfiguration.getConfiguration("validGridList")
        validGridWeight = objConfiguration.getConfiguration("validGridWeight")
        stopInfo = objConfiguration.getConfiguration("stopInfo")
        psgrStart = objConfiguration.getConfiguration("psgrStart")
        psgrEnd = objConfiguration.getConfiguration("psgrEnd")
        isTerminalOn = objConfiguration.getConfiguration("isTerminalOn")
        isVisualizerOn = objConfiguration.getConfiguration("isVisualizerOn")

        isShowFigure = objConfiguration.getConfiguration("isShowFigure")
        isSaveFigure = objConfiguration.getConfiguration("isSaveFigure")
        isDBsave = objConfiguration.getConfiguration("isDBsave")
        
        if EDServiceRate == 0:
            EDService = False
        else :
            EDService = True

        
        ## init GlobalVar ##
        self.globalVar = GlobalVar(isTerminalOn, graph_data, node_data, shuttleInfo, validGridList, validGridWeight, stopInfo,  jsonPath, self.numShuttle, self.scenarioID, isDBsave)

        if prevAnalysisModel == None :
            ## init Analyzer ##
            self.objAnalyzer = Analyzer("Analyzer", self.globalVar, psgrStart, psgrEnd, self.iter, self.maxSim, self.numShuttle, self.maxShuttle, isShowFigure, isSaveFigure, self.isShuttleChange, EDService, EDServiceRate, psgrPercent)
        else:
            prevAnalysisModel.setSimulationIteration(self.iter)
            prevAnalysisModel.setShuttleIteration(self.numShuttle)
            prevAnalysisModel.setGlobalVar(self.globalVar)
            self.objAnalyzer = prevAnalysisModel
            
        self.addModel(self.objAnalyzer)
        self.prevAnalysisModel = self.objAnalyzer
        

        self.objGenerator = Generator("Generator", self.globalVar, EDService, EDServiceRate, genEndTime, psgrPercent)
        self.addModel(self.objGenerator)
        
        self.objDspPpManager = DspPpManager("DspPpManager", self.globalVar)
        self.addModel(self.objDspPpManager)
        
        self.objScheduleManager = ScheduleManager("ScheduleManager", self.globalVar)
        self.addModel(self.objScheduleManager)

        self.objCustomerQueue = CustomerQueue("CustomerQueue", self.globalVar)
        self.addModel(self.objCustomerQueue)
        
        if maxSim > 1 and isVisualizerOn == True:
            isVisualizerOn = False
            print("MonteCarlo Simulation으로 인한 visualizer는 off 되었습니다.")
        # self.objVisualizer = Visualizer("Visualizer", self.globalVar, isVisualizerOn, jsonPath, self.iter, renderTime, simulationMode)
        # self.addModel(self.objVisualizer)
        self.addCoupling(self.objGenerator, "Passenger", self.objCustomerQueue, "Passenger")
        self.addCoupling(self.objDspPpManager, "DispatchRoute_Res", self.objScheduleManager, "DispatchRoute_Res")
        self.addCoupling(self.objScheduleManager, "DispatchRoute_Req", self.objDspPpManager, "DispatchRoute_Req")
        self.addCoupling(self.objCustomerQueue, "Call", self.objScheduleManager, "Call")
        self.addCoupling(self.objCustomerQueue, "SimumlationComplete", self.objAnalyzer, "SimumlationComplete")
        self.addCoupling(self.objScheduleManager, "Transit", self.objCustomerQueue, "Transit")
        
        ## init Shuttles ##
        self.objShuttle = []
        for info in shuttleInfo:
            objShuttle = Shuttle(info['shuttleID'], self.globalVar, info['boardingTime'])
            self.objShuttle.append(objShuttle)
            self.addModel(objShuttle)
            self.addCoupling(objShuttle, "Transit", self.objCustomerQueue, "Transit")
            self.addCoupling(self.objScheduleManager, "Schedule", objShuttle, "Schedule")
            # self.addCoupling(objShuttle, "CurPath", self.objVisualizer, "CurPath")

            

