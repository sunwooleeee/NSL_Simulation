# 승객의 탑승 요청을 실시간으로 받아서 generator에 전달하는 모듈 
from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel
from DataServer import KPIDataSaver
import threading,json,socket

class recv_request_server(DEVSAtomicModel):
    def __init__(self,strID,globalVar):
        super().__init__(strID)
        # set Global Variables
        self.globalVar = globalVar #data/GlobalVar.py 에서 GlobalVar 객체를 전역변수로서 선언한 후 가져온다. 
        self.kpi_saver = KPIDataSaver() #중요한 결과를 저장하기 위한 객체 설정 
        self.stateList = ["OPEN"] # 상태 리스트 
        self.state = self.stateList[0]
        self.dataqueue=[]
        
        #ouput ports
        self.addOutputPort("Request") 

        # self variables
        self.addStateVariable("strId",strID)

        #start server 
        self.server_thread=threading.Thread(target=self.start_server,daemon=True)
        self.server_thread.start()

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
                self.dataqueue.append(self.data)
                if not self.data:
                    print("연결 종료: 강제 종료")
                    break

        except Exception as e:
            print(f"[서버:{self.addr}] 오류: {e}")

        finally:
            self.client_socket.close()
            
        self.client_socket.close()
        self.server_socket.close()

    def funcOutput(self):
        if self.state=="OPEN":
            if self.dataqueue:
                recv_data=self.dataqueue.pop(0)
                try:
                    parsed_data = json.loads(recv_data)
                    self.addOutputEvent("Request", parsed_data)

                except json.JSONDecodeError:
                        print("JSON 파싱 오류, raw_data:", self.data)
            else:
                 return True


        else:
            print("ERROR at recv_request_server OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False
        
    def funcTimeAdvance(self):
        return 1