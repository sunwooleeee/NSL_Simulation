from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel
from DataServer import KPIDataSaver
import numpy as np
import random
import math
import pandas as pd
import time 

class Generator(DEVSAtomicModel):
    # 인자 설명 
    # strID: devs 모델의 id, globalVar: Data/GlobalVar.py의 Global 객체, EDService,EDSserviceRate: 모름, genEndTime: 종료 시간?, psgrPercent: 모름   
    def __init__(self, strID, globalVar, EDService, EDServiceRate, genEndTime, psgrPercent):
        super().__init__(strID)

        # set Global Variables
        self.globalVar = globalVar #data/GlobalVar.py 에서 GlobalVar 객체를 전역변수로서 선언한 후 가져온다. 
        self.kpi_saver = KPIDataSaver() #중요한 결과를 저장하기 위한 객체 설정 
        self.stateList = ["GEN", "WAIT"] # 상태 리스트 
        self.state = self.stateList[0] # 처음 상태를 gen으로 설정 , 의문점 generator 안에서 state와 AtomicModel 객체의 states={} 는 어떤 차이가 있지? 

        # input Ports

        # output Ports
        self.addOutputPort("Passenger")     #def addOutputPort(self, varOutput):
                                            #    self.outputs.append(varOutput) 즉 output이라는 lst에 Passenger 삽입 

        # self variables
        self.addStateVariable("strID", strID)  #def addStateVariable(self, varState, varStateValue):
                                               #      self.states[varState] = varStateValue, 
                                               # states={"strId":strid} 이런 형식으로 데이터 저장, 이게 의미하는 바가 무엇이지?
                                               # 아마 추측상 상태 천이를 위한 변수와는 달리, 여러 부가 정보를 저장해놓은 딕셔너리일것같다는 생각  

        # 
        # 정확히 어떤 것들을 의미하는지는 모르겠지만, 필요한 여러 정보들을 전역변수로부터 가져온다고 볼 수 있다. -> 정류장 노드,                                        
        self.genInfo = self.globalVar.getGeneratorInfo() #이 함수가 무엇을 하는 함수인지 확인
                                                        #def getGeneratorInfo(self):
                                                        #        return self.genInfo 
                                                        # sef.geninfo에는 아래와 같은 변수가 존재한다. dic형식으로 존재 
                                                        #self.genInfo["validGridList"] = validGridList : 탑승자가 발생할 수 있는 위치 
                                                        #self.genInfo["validGridWeight"] = validGridWeight : 탑승자가 해당 위치에서 발생할 확률 
                                                        #self.genInfo["stopInfo"] = stopInfo , 정류정 노드에 대한 정보 
                                                        # 여기서 validGridlist,validFridWeight,stopinfo가 무엇인지 파악할 필요가 있다. 
        self.stopInfo = self.genInfo["stopInfo"]
        self.genEndTime = 999999999999  # 무한대로 바꿀 필요가 있다. 
        
        

        # variables
        self.psgrID = 0
        self.psgrCount = 0
        
    # 외부 천이 함수는 아직 기능 없음, DEVSAtomicModel.py에서 정의된 함수인데 이게 어떻게 작동을 해야하는건지 파악할 필요가 있다.
    # 소켓 통신을 통해서 funcOutput에 있는 값을 가져올 수 있도록 만들어야한다. 
    # 소켓 통신을 통해서 값을 가져오게 되는 경우 self.state="GEN" 으로 변경  
    def funcExternalTransition(self, strPort, objEvent):
        print("ERROR at Generator ExternalTransition: #{}".format(self.getStateValue("strID")))
        print("inputPort: {}".format(strPort))
        print("CurrentState: {}".format(self.state))
        return False
    #fcunExternalTransition에서 얻어온 값을 가지고 승객 객체를 만든 후 해당 값을 queue에 넣어야한다. 
    def funcOutput(self):
        if self.state == "GEN":
            self.psgrID = self.psgrID + 1   #psgr을 하나씩 뽑아낼때마다 id의 값을 1씩 증가시킨다 
            psgrNum = 1 # 일단 승객의 수는 1명으로 고정 
            self.psgrCount = self.psgrCount + psgrNum #psgr count 지금까지의 누적 승객 수 계산 

            #기존의 데이터를 기반으로 출발 위치와 도착 위치의 좌표 설정 , x는 430~1430 으로 ,y는 1510~ 2280사이의 값으로 설정
            dep_x, dep_y = 430.12,1453.23
            arr_x, arr_y = 1783.13,1934.22
                
            ## 사용 안할거임 오류 방지를 위해서 남겨놓은 것 
            psgrEDS = False
            
            #출발해야하는 노드와 도착해야하는 노드를 globalVar에 저장 
            dep_node = self.globalVar.add_dynamic_node(dep_x, dep_y)
            arr_node = self.globalVar.find_nearest_nodes(arr_x, arr_y)
            arr_node = arr_node[0] #arr_node는 리스트 형식으로 노드와 가장 가까운 애들부터 정렬되어있다. 이 중 가장 가까운 노드가 [0] 에 있다

            # 전역변수 psgrwaitingqueue에 승객 객체를 넣어서 대기하도록 한다. 
            self.globalVar.setTargetPsgr(self.psgrID, psgrNum, dep_node, arr_node, psgrEDS, self.getTime())
                
            #데이터 저장을 위한 코드 
            if self.globalVar.isDBsave == True:
                self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'psgrNum': psgrNum})
                self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'dep_node' : dep_node})
                self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'arr_node' : arr_node})
                calltime = self.getTime()
                self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'calltime' : calltime}) 
            self.addOutputEvent("Passenger", self.psgrID)
            self.globalVar.printTerminal("[{}][{}] Passenger #{}:{} generated #{} to #{}".format(self.getTime(), self.getStateValue("strID"), self.psgrID,psgrNum,dep_node, arr_node))

        else:
            print("ERROR at Generator OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False


    
    #GEN 상태인 경우 WIAT  
    def funcInternalTransition(self):
        if self.state == "GEN":
            self.state="WAIT"
            return True
        else:
            return True
    # GEN 상태의 경우 arrivalTime의 시간만큼 대기 
    # WAIT 상태의 경우 무한대의 시간동안 대기 
    def funcTimeAdvance(self):
        if self.state == "GEN":
            return 0 # 승객 생성 후 바로 내부천이 
        else:
            return 9999999999 #wait 에서 gen으로의 내부 천이는 불가능 
