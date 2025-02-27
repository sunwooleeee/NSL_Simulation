# 승객의 탑승 요청을 실시간으로 받아서 generator에 전달하는 모듈
from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel
from DataServer import KPIDataSaver
import threading, json, socket

class recv_request_server(DEVSAtomicModel):
    def __init__(self, strID, globalVar):
        super().__init__(strID)
        # set Global Variables
        self.globalVar = globalVar
        self.kpi_saver = KPIDataSaver()
        self.stateList = ["OPEN","CLOSE"]
        self.state = self.stateList[0]
        self.dataqueue = []

        # Output ports
        self.addOutputPort("Request")

        # self variables
        self.addStateVariable("strId", strID)

        # Start server in a separate thread
        self.server_thread = threading.Thread(target=self.start_server, daemon=True)
        self.server_thread.start()

    def start_server(self):
        self.host = "127.0.0.1"
        self.port = 8888
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"서버가 {self.host}:{self.port}에서 대기 중...")

        while True:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"{addr}에서 연결됨")

                # 새 클라이언트가 들어올 때마다 별도 스레드에서 처리
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, addr),
                    daemon=True
                )
                client_thread.start()

            except Exception as e:
                print(f"[서버:{addr}] 오류: {e}")
                break

        self.server_socket.close()
        self.state=self.stateList[1]

    def handle_client(self, client_socket, addr):
        """
        각 클라이언트의 요청을 받아 dataqueue에 저장
        """
        try:
            while True:
                data = client_socket.recv(1024).decode().strip()
                if not data:
                    print(f"{addr} 연결 종료")
                    break
                self.dataqueue.append(data)
                print(f"{addr} -> 수신 데이터: {data}")

        except Exception as e:
            print(f"[서버:{addr}] 오류: {e}")

        finally:
            client_socket.close()

    def funcOutput(self):
        if self.state == "OPEN":
            if self.dataqueue:
                recv_data = self.dataqueue.pop(0)
                try:
                    parsed_data = json.loads(recv_data)
                    self.addOutputEvent("Request", parsed_data)
                except json.JSONDecodeError:
                    print("JSON 파싱 오류, raw_data:", recv_data)
            else:
                return True

        else:
            print("ERROR at recv_request_server OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcTimeAdvance(self):
        if self.state=="OPEN":
            return 1
        else:
            return 99999999999
