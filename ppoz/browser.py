from bs4 import BeautifulSoup
import json
import requests
import config.config as config


class PPOZ_Browser(object):
    """docstring for ClassName"""

    def __init__(self, mode):
        super(PPOZ_Browser, self).__init__()
        # logging.basicConfig()
        # logging.getLogger().setLevel(logging.DEBUG)

        # requests_log = logging.getLogger("requests.packages.urllib3")
        # requests_log.setLevel(logging.DEBUG)
        # requests_log.propagate = True
        # http_client.HTTPConnection.debuglevel = 1
        self.br = requests.Session()
        self.br.headers.update({
                                   'User-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/66.0.3359.139 Chrome/66.0.3359.139 Safari/537.36'})
        if mode == 'test':
            self.pkurp_address = config.ppoz_test_address
            self.pkurp_user_name = config.ppoz_test_user_name
            self.pkurp_user_pass = config.ppoz_test_user_pass

            self.cia_url_idp = config.cia_test_url_idp
        # self.podsistema=podsistema
        elif mode == 'prom':
            self.ppoz_address = config.ppoz_prom_address
            self.ppoz_user_name = config.ppoz_prom_user_name
            self.ppoz_user_pass = config.ppoz_prom_user_pass

            self.cia_url_idp = config.cia_prom_url_idp
        # self.podsistema=podsistema

        else:
            return False

        return

    def get_appeal_numbers(self, url, post_data):
        requests_list = []
        for i in range(0, 1):
            resp = self.br.post(url, json=post_data, headers={'Content-Type': 'application/json'})
            resp_json = json.loads(resp.text)
            # print(resp_json)
            for requests in resp_json['requests']:
                print("'%s'," % requests['appealNumber'])
                requests_list.append(requests['appealNumber'])
        return requests_list

    def init_module(self, podsistema, user_name, password):
        # if not self.br:
        # self.br = requests.Session()
        # self.br.headers.update({'User-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/66.0.3359.139 Chrome/66.0.3359.139 Safari/537.36'})
        if podsistema == 'ppoz':
            # url_podsistema=''
            # resp=self.br.get(url_podsistema)
            resp = self.br.get("http://{0}:9001/manager///login".format(self.ppoz_address))
        # time.sleep(5)
        soup = BeautifulSoup(resp.text, "lxml")
        for param in soup.findAll('input'):
            if param['name'] == 'RelayState':
                RelayState = param['value']
            if param['name'] == 'SAMLRequest':
                SAMLRequest = param['value']
        action = soup.find('form')['action']
        resp = self.br.post(action, data={'RelayState': RelayState, 'SAMLRequest': SAMLRequest})
        resp = self.br.post(url=self.cia_url_idp + 'checkPassword',
                            data={'userLogin': user_name, 'userPassword': password})
        if 'Пароль неверный.' in resp.text:
            print('Пароль неверный.')
        # send_doc_to_message('Пароль неверный.')
        if "Превышено количество одновременных сессий пользователя. Закрыть предыдущую сессию и продолжить?" in resp.text:
            # br.headers.update({'referer': url_cia_idp+'checkPassword'})
            resp = self.br.post(url=self.cia_url_idp + 'checkPassword?forceAuth=true', params={'forceAuth': True},
                                data={'userLogin': user_name, 'userPassword': password})
        # print(resp.text)
        soup = BeautifulSoup(resp.text, "lxml")
        for param in soup.findAll('input'):
            if param['name'] == 'RelayState':
                RelayState = param['value']
            if param['name'] == 'SAMLResponse':
                SAMLResponse = param['value']
        action = soup.find('form')['action']
        resp = self.br.post(action, {'RelayState': RelayState, 'SAMLResponse': SAMLResponse})
        # print (resp.text)

        return
