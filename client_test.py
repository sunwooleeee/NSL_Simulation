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
        
        # 승객 데이터 전송 (예: 1회 전송)
        for i in range(1):
            # 승객 데이터 랜덤 생성
            # 승객 배차 성공 버전 
            dep_x = round(random.uniform(1000, 1200), 2)  # 출발지 X 좌표 (임의 범위)
            dep_y = round(random.uniform(1000, 1200), 2)   # 출발지 Y 좌표 (임의 범위)
            arr_x = round(random.uniform(800, 1000), 2)   # 도착지 X 좌표 (임의 범위)
            arr_y = round(random.uniform(800, 1000), 2)   # 도착지 Y 좌표 (임의 범위)
                            # 승객 수 (1~3 랜덤)


            #승객 배차 실패 버전 
            #dep_x = round(random.uniform(100000, 120000), 2)  # 출발지 X 좌표 (임의 범위)
            #dep_y = round(random.uniform(100000, 120000), 2)   # 출발지 Y 좌표 (임의 범위)
            #arr_x = round(random.uniform(800000, 100000), 2)   # 도착지 X 좌표 (임의 범위)
            #arr_y = round(random.uniform(800000, 100000), 2)


            psgrNum = random.randint(1, 3)
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
            client_socket.sendall(json_data.encode('utf-8'))
            print(f"[전송] {json_data}")
            
            time.sleep(1)  # 지속 송신을 위한 대기 시간
        
        # 데이터 전송 완료 후 서버 응답 대기
        print("서버 응답 대기 중...")
        response_data = client_socket.recv(1024)
        if not response_data:
            print("서버로부터 응답이 없습니다.")
        else:
            response_text = response_data.decode('utf-8').strip()
            try:
                response_json = json.loads(response_text)
                # 서버가 전송한 데이터 형식에 따른 출력 처리
                if response_json.get("ShuttleID") is not None:
                    print(f"[수신] 할당된 셔틀 ID: {response_json['ShuttleID']}")
                elif response_json.get("message") is not None:
                    print(f"[수신] 오류 메시지: {response_json['message']}")
                else:
                    print(f"[수신] 알 수 없는 데이터 형식: {response_json}")
            except json.JSONDecodeError as e:
                print("수신 데이터 JSON 파싱 오류:", e)
    
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
