from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel
from DataServer import KPIDataSaver
import numpy as np
import random
import math
import pandas as pd

class Generator(DEVSAtomicModel):
    def __init__(self, strID, globalVar, EDService, EDServiceRate, genEndTime, psgrPercent):
        super().__init__(strID)

        # set Global Variables
        self.globalVar = globalVar
        self.kpi_saver = KPIDataSaver()
        self.stateList = ["GEN", "WAIT"]
        self.state = self.stateList[0]

        # input Ports

        # output Ports
        self.addOutputPort("Passenger")

        # self variables
        self.addStateVariable("strID", strID)

        self.genInfo = self.globalVar.getGeneratorInfo()
        self.validGridList = self.genInfo["validGridList"]
        self.validGridWeight = self.genInfo["validGridWeight"]
        self.stopInfo = self.genInfo["stopInfo"]
        self.genEndTime = genEndTime
        
        self.EDServiceRate = EDServiceRate
        
        if self.EDServiceRate == 0:
            self.EDService = False
        else :
            self.EDService = True
        
        
        self.genProbability  = [2,0.5,3,0.3,4,0.2]
        
        for info in self.stopInfo:
            stop_node_ids = info['stopNodeID']
            stop_count = info['stopCount']
            selected_nodes = random.sample(stop_node_ids, min(len(stop_node_ids), stop_count))
            info['stopNodeID'] = selected_nodes
            
        self.hourly_ratios = self.load_time_ratios()

        self.timeTable = self.simulate_passenger_arrivals(self.hourly_ratios, 652)
        self.dep_arr_data = self.process_demand_data()

        # variables
        self.psgrID = 0
        self.psgrCount = 0
        
        self.arrivalTime = self.timeTable[0]
        

    def funcExternalTransition(self, strPort, objEvent):
        print("ERROR at Generator ExternalTransition: #{}".format(self.getStateValue("strID")))
        print("inputPort: {}".format(strPort))
        print("CurrentState: {}".format(self.state))
        return False

    def funcOutput(self):
        if self.state == "GEN":
            if self.getTime() < self.genEndTime :
                self.psgrID = self.psgrID + 1
                
                psgrNum = int(np.random.choice(self.genProbability[0::2], p=self.genProbability[1::2]))
                self.psgrCount = self.psgrCount + psgrNum
                
                if len(self.timeTable) != 1:
                    self.arrivalTime = self.timeTable[1] - self.timeTable[0]
                    self.timeTable.pop(0)
                else :
                    self.arrivalTime = 99999999

                current_hour = self.getTime() // 3600
                dep_hour_str = f"{current_hour:02d}_승차"  # 예: '00_승차'
                arr_hour_str = f"{current_hour:02d}_하차"  # 예: '00_승차'

                dep_x, dep_y = self.select_node(dep_hour_str)
                arr_x, arr_y = self.select_node(arr_hour_str)
                

                if self.EDService == True: 
                    if random.random() < self.EDServiceRate :
                        psgrEDS = True
                    else :
                        psgrEDS = False
                else :
                    psgrEDS = False

                dep_node = self.globalVar.add_dynamic_node(dep_x, dep_y)
                arr_node = self.globalVar.find_nearest_nodes(arr_x, arr_y)
                arr_node = arr_node[0]

                # org_node_lst = self.globalVar.getNearestNode(dep_node, 10)

                self.globalVar.setTargetPsgr(self.psgrID, psgrNum, dep_node, arr_node, psgrEDS, self.getTime())
                
                if self.globalVar.isDBsave == True:
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'psgrNum': psgrNum})
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'dep_node' : dep_node})
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'arr_node' : arr_node})
                    calltime = self.getTime()
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'calltime' : calltime})
                else:
                    pass

                self.addOutputEvent("Passenger", self.psgrID)
                self.globalVar.printTerminal("[{}][{}] Passenger #{}:{} generated #{} to #{}".format(self.getTime(), self.getStateValue("strID"), self.psgrID,psgrNum,dep_node, arr_node))
            return True
        else:
            print("ERROR at Generator OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcInternalTransition(self):
        if self.state == "GEN":
            if len(self.timeTable) != 0 :
                self.state = self.stateList[0]
            else:
                psgr = self.globalVar.getPsgrInfoByID(self.psgrID)
                psgr.setlastPsgr()
                self.state = self.stateList[1]
            return True
        else:
            print("ERROR at Generator InternalTransition: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcTimeAdvance(self):
        if self.state == "GEN":
            return self.arrivalTime
        else:
            return 999999999999


    def simulate_arrival_times(self, rate_per_hour, total_time, seed):
        np.random.seed(seed)
        mean_arrival_rate = 3600 / rate_per_hour
        inter_arrival_times = np.random.exponential(mean_arrival_rate, int(rate_per_hour * total_time / 3600))
        arrival_times = np.cumsum(inter_arrival_times)
        arrival_times = arrival_times[arrival_times <= total_time]
        return arrival_times
        

    def simulate_passenger_arrivals(self, hourly_traffic_ratios, total_passengers):
        all_arrivals = []
        
        for hour, ratio in hourly_traffic_ratios.items():
            if ratio > 0:
                hour_index = int(hour[:2])  # 'XX(승차)'에서 'XX' 부분 추출
                expected_passengers = total_passengers * ratio
                lambda_hour = expected_passengers / 3600  # 1시간 = 3600초

                # 포아송 프로세스를 사용하여 도착 시간 생성
                arrival_time = hour_index * 3600  # 시간대의 시작 시간
                while arrival_time < (hour_index + 1) * 3600:
                    inter_arrival_time = np.random.exponential(1 / lambda_hour)
                    arrival_time += inter_arrival_time
                    if arrival_time >= (hour_index + 1) * 3600:
                        break
                    all_arrivals.append(int(arrival_time))

        all_arrivals.sort()  # 도착 시간 정렬

        # 동일한 시간에 도착하는 승객들의 시간을 미세하게 조정
        for i in range(1, len(all_arrivals)):
            if all_arrivals[i] <= all_arrivals[i-1]:
                all_arrivals[i] = all_arrivals[i-1] + 1

        return all_arrivals


    def load_time_ratios(self):
        # 시간대별로 정규화된 비율 데이터를 로드합니다.
        # 실제 데이터로 교체해야 합니다.
        # 데이터 형식은 딕셔너리로, 키는 시간대(정수), 값은 해당 시간대의 비율 리스트입니다.
        # 예시 데이터를 사용합니다.
        data = pd.read_excel('JSON/Demand.xlsx', header=1)
        demand_data = pd.DataFrame(data)

        boarding_columns = [col for col in demand_data.columns if '승차' in col and 'Unnamed' not in col]
        alighting_columns = [col for col in demand_data.columns if '하차' in col and 'Unnamed' not in col]

        # 승차와 하차 데이터 선택
        boarding_data = demand_data[boarding_columns].astype(float)
        alighting_data = demand_data[alighting_columns].astype(float)

        # 승차와 하차 데이터의 인덱스 정렬 (하차 시간 열 이름에서 '승차'로 변경하여 일치시키기)
        alighting_data.columns = boarding_data.columns

        # 승차와 하차 데이터 합산
        total_traffic_data = boarding_data + alighting_data

        # 각 시간대별 승객 수의 총합 계산
        hourly_total_traffic = total_traffic_data.sum()

        # 각 시간대의 승객 비율 계산 (총 승객 수 대비 각 시간대 승객 수의 비율)
        total_traffic_sum = hourly_total_traffic.sum()
        hourly_traffic_ratios = hourly_total_traffic / total_traffic_sum

        # 결과 출력
        hourly_traffic_ratios

        return hourly_traffic_ratios

    def process_demand_data(self):
        # 데이터 불러오기
        data = pd.read_excel('JSON/Demand.xlsx', header=1)
        df = pd.DataFrame(data)

        # 위도와 경도를 기반으로 x, y 좌표 계산
        df['y'] = ((df['위도'] - 37) * 10000).astype(int)
        df['x'] = ((df['경도'] - 127) * 10000).astype(int)

        # 새 DataFrame 초기화
        new_df = pd.DataFrame()
        new_df['x'] = df['x']
        new_df['y'] = df['y']

        # 모든 시간대에 대한 승차 및 하차 데이터 추가
        for time in range(24):
            hour_str = f"{time:02d}"  # 시간을 '00', '01', ..., '23' 형식으로 포맷
            boarding_col = f"{hour_str}(승차)"
            alighting_col = f"{hour_str}(하차)"
            
            # 승차 및 하차 데이터가 존재하는지 확인하고 추가
            if boarding_col in df.columns and alighting_col in df.columns:
                boarding_data = df[boarding_col].replace(0, 0.0001)
                alighting_data = df[alighting_col].replace(0, 0.0001)
                new_df[f"{hour_str}_승차"] = boarding_data
                new_df[f"{hour_str}_하차"] = alighting_data

        # 결과 DataFrame 반환
        return new_df
    
    def select_node(self, hour_str):
        if hour_str in self.dep_arr_data.columns:
            # 시간대에 맞는 승차 데이터로 가중치 설정
            valid_data = self.dep_arr_data[['x', 'y', hour_str]]
            
            # 가중치에 따라 출발 위치 선택
            selected_stop = valid_data.sample(weights=valid_data[hour_str], n=1)
            node_x = selected_stop['x'].values[0]
            node_y = selected_stop['y'].values[0]
            jitter = 10  # 변동 범위 조정 가능
            node_x += random.uniform(-jitter, jitter)
            node_y += random.uniform(-jitter, jitter)

        else:
            # 데이터 없음 시 무작위 위치
            node_x = random.uniform(430, 1430)
            node_y = random.uniform(1510, 2280)
        
        return node_x, node_y