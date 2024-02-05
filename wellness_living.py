import requests
import json
from datetime import datetime
from hashlib import sha256
from hashlib import sha3_512
from urllib.parse import urlparse
from easysettings import EasySettings
import sys

from requests.adapters import HTTPAdapter
from urllib3 import Retry

#from forms.WindowTools import WindowTools

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)

O_SETTING = EasySettings("settings.conf")
config_settings = EasySettings("settings.conf")

class Config:
  AUTHORIZE_CODE = config_settings.get('AUTHORIZE_CODE')
  AUTHORIZE_ID = config_settings.get('AUTHORIZE_ID')
  COOKIE_PERSISTENT = 'sp'
  COOKIE_TRANSIENT = 'st'
  URL_BASE = 'https://staging.wellnessliving.com/'

class RequestModel:
  a_cookies = {}
  s_resource = None

  def __init__(self, s_resource):
    super().__init__()

    self.s_resource = s_resource

  def post(self, a_get=None, a_post=None, a_file=None):
    return self._request('post', a_get, a_post, a_file)

  def get(self, a_get=None):
    return self._request('get', a_get)

  def _request(self, s_method, a_get=None, a_post=None, a_file=None):
    if not s_method in ['get', 'post']:
      raise ValueError('Method invalid')

    if a_get is None:
      a_get = {}
    if a_post is None:
      a_post = {}
    if a_file is None:
      a_file = {}

    a_variable = {}
    for s_key in a_get:
      a_variable[s_key] = a_get[s_key]
    for s_key in a_post:
      a_variable[s_key] = a_post[s_key]
    for s_key in a_file:
      d_file_hash = sha256()

      with open(a_file[s_key], 'rb') as f:
        while True:
          data = f.read(65536)
          if not data:
            break
          d_file_hash.update(data)

      a_variable[s_key] = d_file_hash.hexdigest()
      a_file[s_key] = open(a_file[s_key], 'rb')

    url_request = Config.URL_BASE + self.s_resource
    dtu_request = datetime.utcnow()

    s_cookies = O_SETTING.get('cookies')
    has_cookies = False
    if s_cookies:
      a_cookies_temp = json.loads(s_cookies)
      if len(a_cookies_temp):
        has_cookies = True
        self.a_cookies = a_cookies_temp

    a_header = {}
    a_header['X-Signature-Date'] = str(dtu_request.strftime("%a, %d %b %Y %H:%M:%S GMT"))

    a_url = urlparse(url_request)
    a_header['Authorization'] = ','.join([
      '20150518',
      Config.AUTHORIZE_ID,
      '',
      self.signatureCompute({
        'a_variable': a_variable,
        'dt_time': str(dtu_request.strftime('%Y-%m-%d %H:%M:%S')),
        's_code': Config.AUTHORIZE_CODE,
        's_host': a_url.netloc,
        's_id': Config.AUTHORIZE_ID,
        's_method': s_method.upper(),
        's_resource': self.s_resource
      })
    ])

    if s_method == 'get':
      response = session.get(url_request, headers=a_header, params=a_get, cookies=self.a_cookies)
    else:
      response = session.post(url_request, headers=a_header, params=a_get, files=a_file, data=a_post,
                               cookies=self.a_cookies)

    for s_key in a_file:
      a_file[s_key].close()

    try:
      a_result = response.json()
    except json.JSONDecodeError:
      a_result = {
        'status': 'json-invalid',
        'message': response.text,
        'header': response.headers
      }

    # if a_result['status'] == 'user-out' maybe open login page.
    if a_result['status'] == 'notepad-create' or a_result['status'] == 'user-out' or a_result['status'] == 'csrf':
      has_cookies = False

    if not has_cookies:
      self.a_cookies = {}
      for key, value in response.cookies.items():
        self.a_cookies[key] = value

      O_SETTING.setsave('cookies', json.dumps(self.a_cookies))

    if a_result['status'] == 'internal':
      WindowTools.errorBox(a_result['message'])

    return a_result

  def signatureCompute(self, a_data):
    a_signature = []
    a_signature.append('Core\\Request\\Api::20150518')
    a_signature.append(a_data['dt_time'])
    a_signature.append(a_data['s_code'])
    a_signature.append(a_data['s_host'])
    a_signature.append(a_data['s_id'])
    a_signature.append(a_data['s_method'])
    a_signature.append(a_data['s_resource'])

    # COOKIE_PERSISTENT
    if Config.COOKIE_PERSISTENT in self.a_cookies:
      a_signature.append(self.a_cookies[Config.COOKIE_PERSISTENT])
    else:
      a_signature.append('')

    # COOKIE_TRANSIENT
    if Config.COOKIE_TRANSIENT in self.a_cookies:
      a_signature.append(self.a_cookies[Config.COOKIE_TRANSIENT])
    else:
      a_signature.append('')

    # TODO $a_variable = WlModelRequest::signatureArray($a_data['a_variable']);
    for s_key in sorted(a_data['a_variable']):
      a_signature.append(s_key + '=' + a_data['a_variable'][s_key])

    return sha256(str("\n".join(a_signature)).encode('utf-8')).hexdigest()


def passwordHash(s_password, s_notepad):
  a_delimiter = ['r', '4S', 'zqX', 'zqiOK', 'TLVS75V', 'Ue5aLaIIG75', 'uODJYM2JsCX4G', 'kt58wZfHHGQkHW4QN',
                 'Lh9Fl5989crMU4E7P6E']

  s_hash = ''
  for s_delimiter in a_delimiter:
    s_hash = s_hash + s_delimiter + s_password
  s_hash = sha3_512(str(s_hash).encode('utf-8')).hexdigest()

  return sha3_512(str(s_notepad + s_hash).encode('utf-8')).hexdigest()

o_model = RequestModel('Wl/Session/Environment.json')
a_result = o_model.get()
#print(a_result)

if not a_result['status'] == 'ok' or a_result['uid'] is None:
  # Perform login.
  o_model_notepad = RequestModel('Core/Passport/Login/Enter/Notepad.json')

  a_result_notepad = o_model_notepad.get()

  print(a_result_notepad)

  s_login = config_settings.get('s_login')
  s_password = config_settings.get('s_password')

  #if not a_result_notepad['status'] == 'ok':
  #  Error while get notepad.

  o_model_enter = RequestModel('Core/Passport/Login/Enter/Enter.json')

  a_result_login = o_model_enter.post(
    a_post={
      's_login': s_login,
      's_notepad': a_result_notepad['s_notepad'],
      's_password': passwordHash(s_password, a_result_notepad['s_notepad'])
    }
  )
  print(a_result_login)

  #if not a_result_login['status'] == 'ok':
  #  Error while login.

  # Successful login
#else:
#  Already logged.
if __name__ == "__main__":
    # Check if a member ID was provided as a command-line argument
    if len(sys.argv) > 1:
        member_id = sys.argv[1]  # Use the member ID from the command line
    else:
        member_id = config_settings.get('s_member')  # Fallback to the config setting if no argument is provided

    # Initialize the RequestModel with the desired endpoint
    o_model_user = RequestModel('Wl/Integration/DragonFly/Access.json')

    # Use the provided or fallback member ID in the API call
    a_result_user = o_model_user.get(
        a_get={
            'k_location': config_settings.get('k_location'),
            's_member': member_id  # Use the dynamically determined member ID
        }
    )

    # Output the result of the API call
    print(a_result_user)