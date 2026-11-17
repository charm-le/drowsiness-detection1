import os
import time
import urllib.request
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import serial

arduino = serial.Serial('COM11', 9600, timeout=1)
time.sleep(2)

model_path = 'face_landmarker.task'
if not os.path.exists(model_path):
  print('AI 인식 모델 다운로드 중...')
  url = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'
  urllib.request.urlretrieve(url, model_path)
  print('다운로드 완료!')

base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    output_face_blendshapes=True,
    running_mode=vision.RunningMode.IMAGE,
)
detector = vision.FaceLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)

drowsy_count = 0
total_sleep_seconds = 0
eyes_closed_start = None
last_increment_time = 0
is_drowsy = False
last_sent_state = ''

print('실시간 졸음 감지 시스템 실행 중...')

while cap.isOpened():
  success, frame = cap.read()
  if not success:
    break

  frame = cv2.flip(frame, 1)
  rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
  mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
  results = detector.detect(mp_image)

  eyes_closed = False

  if results.face_blendshapes:
    blendshapes = results.face_blendshapes[0]
    left_blink = 0.0
    right_blink = 0.0

    for score in blendshapes:
      if score.category_name == 'eyeBlinkLeft':
        left_blink = score.score
      elif score.category_name == 'eyeBlinkRight':
        right_blink = score.score

    if left_blink > 0.4 and right_blink > 0.4:
      eyes_closed = True

  # 실시간 상태 전송 및 초단위 타이머 로직
  if eyes_closed:
    if eyes_closed_start is None:
      eyes_closed_start = time.time()
      last_increment_time = time.time()
    elif time.time() - eyes_closed_start > 1.5:  # 1.5초 이상 눈 감으면 경고 시작
      if not is_drowsy:
        drowsy_count += 1
        is_drowsy = True

      if time.time() - last_increment_time >= 1.0:
        total_sleep_seconds += 1
        last_increment_time = time.time()

      total_minutes = int(total_sleep_seconds // 60)

      # 눈 감은 상태(CLOSED) 전송
      current_state = f'CLOSED,{drowsy_count},{total_minutes}\n'
      if current_state != last_sent_state:
        arduino.write(current_state.encode('utf-8'))
        last_sent_state = current_state
  else:
    eyes_closed_start = None
    is_drowsy = False

    # 눈 뜬 상태(OPEN) 전송
    current_state = 'OPEN\n'
    if current_state != last_sent_state:
      arduino.write(current_state.encode('utf-8'))
      last_sent_state = current_state

  # --- 화면 표시 (기본 상태 및 카운트/시간) ---
  status_text = 'Status: Drowsy!' if eyes_closed else 'Status: Normal'
  color = (0, 0, 255) if eyes_closed else (0, 255, 0)
  cv2.putText(
      frame,
      status_text,
      (30, 40),
      cv2.FONT_HERSHEY_SIMPLEX,
      0.8,
      color,
      2,
  )
  cv2.putText(
      frame,
      f'Count: {drowsy_count} | Time: {total_sleep_seconds}s',
      (30, 80),
      cv2.FONT_HERSHEY_SIMPLEX,
      0.8,
      (255, 255, 0),
      2,
  )

  # --- [핵심 기능] 횟수 5회 이상 또는 누적 시간 30초 이상일 때: 빨간 박스 + 3초간 경고 후 자동 종료 ---
  if drowsy_count >= 5 or total_sleep_seconds >= 30:
    height, width, _ = frame.shape
    # 1. 화면 테두리를 감싸는 굵은 빨간 박스
    cv2.rectangle(frame, (20, 20), (width - 20, height - 20), (0, 0, 255), 10)

    # 2. 큼직한 경고 글씨 출력
    cv2.putText(
        frame,
        'TAKE A BREAK!',
        (width // 2 - 270, height // 2 - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (0, 0, 255),
        4,
    )
    cv2.putText(
        frame,
        '잠시 쉬어가십시오!',
        (width // 2 - 230, height // 2 + 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (0, 0, 255),
        4,
    )

    # 화면에 경고 창 즉시 렌더링
    cv2.imshow('Drowsiness Detection', frame)
    cv2.waitKey(1)

    # 아두이노에 경고 상태 확실히 전송
    current_state = f'CLOSED,{drowsy_count},{total_minutes}\n'
    arduino.write(current_state.encode('utf-8'))

    # 3초 동안 부저가 울리도록 대기
    time.sleep(3)

    # 반복문 탈출하여 프로그램 종료 준비
    break

  cv2.imshow('Drowsiness Detection', frame)
  if cv2.waitKey(1) & 0xFF == ord('q'):
    break

# 안전하게 자원 해제 및 창 닫기
cap.release()
cv2.destroyAllWindows()
arduino.close()
