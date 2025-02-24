import socket
import json
import time
import random

def send_passenger_data(host, port):
    # 소켓 생성
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # 서버에 연결
        client_socket.connect((host, port))
        print(f"서버({host}:{port})에 연결되었습니다.")
        
        # 무한 반복으로 지속 송신
        passenger_id = 0
        while True:
            # 승객 데이터 랜덤 생성
            dep_x = round(random.uniform(400, 1500), 2)  # 출발지 X 좌표 (임의 범위)
            dep_y = round(random.uniform(1400, 2300), 2) # 출발지 Y 좌표 (임의 범위)
            arr_x = round(random.uniform(1700, 2000), 2) # 도착지 X 좌표 (임의 범위)
            arr_y = round(random.uniform(1900, 2500), 2) # 도착지 Y 좌표 (임의 범위)
            psgrNum = random.randint(1, 3)              # 승객 수 (1~5 랜덤)

            # 데이터 구성 (JSON 형식)
            data = {
                "dep_x": dep_x,    
                "dep_y": dep_y,    
                "arr_x": arr_x,    
                "arr_y": arr_y,    
                "psgrNum": psgrNum 
            }
            
            # JSON 문자열로 변환 및 전송
            json_data = json.dumps(data)
            client_socket.sendall(json_data.encode())
            print(f"[전송] {json_data}")
            
            time.sleep(1)
            # 초 대기 (지속 송신)
            
    
    except KeyboardInterrupt:
        print("\n사용자 종료 요청. 클라이언트를 종료합니다.")
    
    except Exception as e:
        print(f"클라이언트 오류: {e}")
    
    finally:
        client_socket.close()
        print("서버 연결이 종료되었습니다.")

# 클라이언트 실행
if __name__ == "__main__":
    HOST = "127.0.0.1"  # Generator의 서버 IP
    PORT = 8888         # Generator의 서버 포트
    
    send_passenger_data(HOST, PORT)
