'The raspberry pi camera class'

import threading
import random
import time
import logging
import json
from PIL import Image
from picamera2 import Picamera2

import dss.auxiliaries
from dss.auxiliaries.config import config, config_path

class PiCam():


  def __init__(self, info_publish_method, data_publish_method): # Socket or methodf??
    # TODO, why does this not work?
    self.logger = logging.getLogger(__name__)
    self.logger.info('PiCam init method')

    self._name = 'Raspbery pi cam'
    self._status_msg = ''
    self._info_publish = info_publish_method
    self._data_publish = data_publish_method
    self._publish_cv_BB = False
    self._publish_cv_OD = False

    self._cam = Picamera2()


    self._cv_algorithms = ['boundingBox', 'objectDetection']
    #self._cv_algorithm = None
    self._abort_task = False

    # Demonstration of config data
    try:
      calibration = config['sensorCalibration']
      print(f'The sensor calibration data found in config file at: {config_path}, under key sensorCalibration is:')
      print(json.dumps(calibration, indent = 4))
      self.logger.info(f'Calibration data: {calibration}')
    except:
      print('\n WARNING No calibration data found. read the manual and correct config file \n')

    try:
      rtsp_url = config['rtsp']['url']
      print(f'The rtsp-url found from config is: {rtsp_url}')
    except:
      print('The configuraition file is mission the key rtsp, read the documentation!')

    self._main_thread_active = True
    self._thread_main = threading.Thread(target=self._main_thread, daemon=True)
    self._thread_main.start()


  # @property
  # def cv_algorithm(self):
  #   '''Returns the active cv algorithm'''
  #   return self._cv_algorithm

  @property
  def abort_task(self):
    '''This attribute is used to abort a running task'''
    return self._abort_task

  # @cv_algorithm.setter
  # def cv_algorithm(self, value):
  #   if value in self._cv_algorithms:
  #     self._cv_algorithm = value
  #   else:
  #     print(f'Value not valid cv_algorithm: {value}')

  @abort_task.setter
  def abort_task(self, value):
    self._abort_task = value


  def raise_if_aborted(self):
    if self.abort_task:
      self._status_msg = 'the task was aborted'
      raise dss.auxiliaries.exception.AbortTask()

  def test_cam_get_focus(self):
    return 6

  def download_photo(self, index, resolution):
    # Index can be used to download an already take picture. We take a new picture for now
    _ = index
    # Resolution can be used to scale or cut the image for example. We use current setting for now
    _ = resolution

    # The code to take a photo
    camera_config = self._cam.create_still_configuration(main={"size": (1920, 1080)}, lores={"size": (640, 480)}, display="lores")
    self._cam.configure(camera_config)
    self._cam.start()
    time.sleep(1)
    #pil_img = io.BytesIO()
    print('pre capture image')
    img = self._cam.capture_image("main")
    print('post capture_image')

    # Bulid up meta, camera calibration and bounding box can be sent for example.
    # There is an old metadata def in the documentation for DSS_API, 2.5.1
    meta = {"index": 1, "filename": "hardcoded", "x": 10, "y": 20, "z":30, "agl": -1, "heading":0}
    # Publish the image on the provided socket

    self._data_publish(topic = "photo", meta=meta, img=img)
    print('after publish')

  def task_cv_algorithm(self, algorithm):
    self.logger.info('task: cv_algorithm')
    self._status_msg = 'cv_algorithm'
    # Check if task should be aborted already
    self.raise_if_aborted()

    # Init stuff..
    x = 100
    y = 50
    x_min = 0
    x_max = 3000
    y_min = 0
    y_max = 4000
    width = 20
    height = 18

    antispam_ticker = 0
    if algorithm == 'boundingBox':
      # Until exception is thrown by raise_if_aborted
      while True:
        x += random.randint(-10,10)
        y += random.randint(-15,15)

        if x < x_min: x = random.randint(x_min, x_max)
        if x > x_max: x = random.randint(x_min, x_max)
        if y < y_min: y = random.randint(y_min, y_max)
        if y > y_max: y = random.randint(y_min, y_max)

        topic = 'BB'
        message = {}
        message['x'] = x
        message['y'] = y
        message['width'] = width
        message['heighjt'] = height

        if self._publish_cv_BB:
          if antispam_ticker % 10 == 0:
            self._info_publish(topic, {'x': x, 'y': y, 'width': width, 'height': height})
        else:
          print('Calculating boundingBox without publishing result')

        # Loop sleep
        time.sleep(0.1)
        antispam_ticker += 1
        # Check if the task should be aborted, raise exception if so
        self.raise_if_aborted()

    if algorithm == 'objectDetection':
      # Until exception is thrown by raise_if_aborted
      while True:
        width += random.randint(-2,2)
        height += random.randint(-2,2)

        if width < 1 or width > 100: width = 20
        if height < 1 or height > 100: height = 20

        topic = 'OD'
        message = {}
        message['x'] = x
        message['y'] = y
        message['width'] = width
        message['heighjt'] = height

        if self._publish_cv_OD:
          if antispam_ticker % 10 == 0:
            self._info_publish(topic, {'x': x, 'y': y, 'width': width, 'height': height})
        else:
          print('Calculating objectDetection without publishing result')

        # Loop sleep
        time.sleep(0.1)
        antispam_ticker += 1
        # Check if the task should be aborted, raise exception if so
        self.raise_if_aborted()

  def _main_thread(self):
    print('Main thread in picam.py does not do anything now. It just prevents the code from exiting')

    while self._main_thread_active:
      time.sleep(0.5)

    print('Main picam thread EXIT')
