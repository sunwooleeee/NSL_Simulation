from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel
from DataServer import KPIDataSaver
import numpy as np
import random
import math
import pandas as pd
import time 
import socket
import threading
import json

class Generator(DEVSAtomicModel):
    # 인자 설명 
    # strID: devs 모델의 id, globalVar: Data/GlobalVar.py의 Global 객체, EDService,EDSserviceRate: 모름, genEndTime: 종료 시간?, psgrPercent: 모름   
    def __init__(self, strID, globalVar, EDService, EDServiceRate, genEndTime, psgrPercent):
        super().__init__(strID)

        # set Global Variables
        self.globalVar = globalVar #data/GlobalVar.py 에서 GlobalVar 객체를 전역변수로서 선언한 후 가져온다. 
        self.kpi_saver = KPIDataSaver() #중요한 결과를 저장하기 위한 객체 설정 
        self.stateList = ["GEN", "WAIT"] # 상태 리스트 
        self.state = self.stateList[1] # 처음 상태를 gen으로 설정 , 의문점 generator 안에서 state와 AtomicModel 객체의 states={} 는 어떤 차이가 있지? 

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
        # Generator 클래스 초기화 시
        self.genEndTime = float('inf')  # genEndTime을 무한대로 설정

        
        

        # variables
        self.psgrID = 0
        self.psgrCount = 0

        # 서버 시작,스레드를 하나 더 만들어서 실행 
        self.server_thread=threading.Thread(target=self.start_server,daemon=True)
        self.server_thread.start()

    # 사용 안함 
    def funcExternalTransition(self, strPort, objEvent):
        return False
    
    #fcunExternalTransition에서 얻어온 값을 가지고 승객 객체를 만든 후 해당 값을 queue에 넣어야한다. 
    def funcOutput(self):
        if self.state == "GEN":
            self.psgrID = self.psgrID + 1   #psgr을 하나씩 뽑아낼때마다 id의 값을 1씩 증가시킨다 
            self.psgrCount = self.psgrCount + self.psgrNum #psgr count 지금까지의 누적 승객 수 계산 

            ## 사용 안할거임 오류 방지를 위해서 남겨놓은 것 
            psgrEDS = False
            
            #출발해야하는 노드와 도착해야하는 노드를 globalVar에 저장 
            dep_node = self.globalVar.add_dynamic_node(self.dep_x, self.dep_y)
            arr_node = self.globalVar.find_nearest_nodes(self.arr_x, self.arr_y)
            arr_node = arr_node[0] #arr_node는 리스트 형식으로 노드와 가장 가까운 애들부터 정렬되어있다. 이 중 가장 가까운 노드가 [0] 에 있다

            # 전역변수 psgrwaitingqueue에 승객 객체를 넣어서 대기하도록 한다. 
            self.globalVar.setTargetPsgr(self.psgrID, self.psgrNum, dep_node, arr_node, psgrEDS, self.getTime())
                
            #데이터 저장을 위한 코드 
            if self.globalVar.isDBsave == True:
                self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'psgrNum': self.psgrNum})
                self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'dep_node' : dep_node})
                self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'arr_node' : arr_node})
                calltime = self.getTime()
                self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'calltime' : calltime}) 
            self.addOutputEvent("Passenger", self.psgrID)
            self.globalVar.printTerminal("[{}][{}] Passenger #{}:{} generated #{} to #{}".format(self.getTime(), self.getStateValue("strID"), self.psgrID,self.psgrNum,dep_node, arr_node))
            
        else:
            print("ERROR at Generator OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False


    
    #내부 천이 분기점 도달 시, 데이터가 존재하면 GEN 상태로 천이, 그것이 아니라면 WAIT 상태로 천이  
    def funcInternalTransition(self):
        if self.data:
            self.state="GEN" 
            return True
        else:
            self.state="WAIT"
            return True
    # GEN 상태의 경우 승객을 생성하는 시간만큼 대기(정확한 시간을 모르겠어서 일단 2s로 함) -> wallclock 필요 
    # WAIT 상태의 1초 동안 대기 (데이터가 오기를 기다리는 시간) -> 근데 이렇게 시간 남발을 하면 작동은 할텐데, 이 시간이 흘러가는 2s 동안 시뮬레이션이 안돌아가는거 아닌가?
    # 그냥 난 wallclock이 시급함 
 
    def funcTimeAdvance(self):
        if self.state == "GEN":
            return 2 # 승객 생성 후  내부천이  
        else:
            time.sleep(1)
            return 2 # wait 에서 gen으로의 내부 천이는 불가능 
        
    def start_server(self):
        self.host="127.0.0.1"
        self.port=8888
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"서버가 {self.host}:{self.port}에서 대기 중...")

        self.client_socket, self.addr = self.server_socket.accept()
        print(f"{self.addr}에서 연결됨")
        # 받아야 하는 데이터 형식 
        # dep_x, dep_y = 430.12,1453.23
        # arr_x, arr_y = 1783.13,1934.22
        # psgrNum =1 
        
        try:
            while True:
                self.data=self.client_socket.recv(1024).decode().strip()

                if not self.data:
                    print("연결 종료: 강제 종료")
                    break
                try:
                    data = json.loads(self.data)
                    self.dep_x = data["dep_x"]
                    self.dep_y = data["dep_y"]
                    self.arr_x = data["arr_x"]
                    self.arr_y = data["arr_y"]
                    self.psgrNum = data["psgrNum"]

                except json.JSONDecodeError:
                    print("JSON 파싱 오류, raw_data:", data)

        except Exception as e:
            print(f"[서버:{self.addr}] 오류: {e}")

        finally:
            self.client_socket.close()
            
        self.client_socket.close()
        self.server_socket.close()
            
