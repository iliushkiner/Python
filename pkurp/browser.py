from bs4 import BeautifulSoup
import json
import time
import config.config as config
import requests
from dict import dict_doc_name


class PKURP_Browser(object):
    """docstring for ClassName"""

    def __init__(self, mode):
        super(PKURP_Browser, self).__init__()
        # logging.basicConfig()
        # logging.getLogger().setLevel(logging.DEBUG)

        # requests_log = logging.getLogger("requests.packages.urllib3")
        # requests_log.setLevel(logging.DEBUG)
        # requests_log.propagate = True
        # http_client.HTTPConnection.debuglevel = 1
        self.br = requests.Session()
        self.pvd_number = ''
        self.br.headers.update({
            'User-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/66.0.3359.139 Chrome/66.0.3359.139 Safari/537.36'})
        self.curent_edit_record = {}
        self.xml_soup = ''
        self.simple_arest = ''
        self.registry_records_list = []
        self.region = ''
        if mode == 'test':
            self.pkurp_address = config.pkurp_test_address
            self.pkurp_user_name = ''
            self.pkurp_user_pass = ''
            self.cia_url_idp = config.cia_test_url_idp
        elif mode == 'prom':
            self.pkurp_address = config.pkurp_prom_address
            self.pkurp_user_name = ''
            self.pkurp_user_pass = ''
            self.cia_url_idp = config.cia_prom_url_idp
        else:
            return False

        return

    def get_info_for_object_in_egrn(self, kn_number, pvd_number):
        # http://pkurp-app-balancer-01.prod.egrn/api/requests/PKPVD-2019-02-26-115878/registry_records?region=11&limit=10&skip=0
        # url="http://"+self.pkurp_address+'/api/requests/'+self.request_dic['pkpvd_number']+'/registry_records?region=00&limit=1000&skip=0'
        # resp=self.br.get(url)
        # for rec in json.loads(resp.text)['data']:
        #		print(rec['cad_number'])
        # http://pkurp-app-balancer-01.prod.egrn/api/requests/PKPVD-2019-02-26-115878
        # print("awdawdawd")
        dic = {}
        # Права
        url = "http://" + self.pkurp_address + '/api/requests/' + pvd_number + '/find_type_records?region=%s&section_number=%s&type=right_record&limit=1000&skip=0' % (
            self.region, kn_number)
        resp = self.request_url(url)
        # print (url)
        # print (resp.text)

        dic['Права'] = json.loads(resp.text)['data']
        # Ограничения обременения
        url = "http://" + self.pkurp_address + '/api/requests/' + pvd_number + '/find_type_records?region=%s&section_number=%s&type=restrict_record&limit=10&skip=0' % (
            self.region, kn_number)
        resp = self.request_url(url)
        dic['Ограничения обременения'] = json.loads(resp.text)['data']
        # Сделки
        url = "http://" + self.pkurp_address + '/api/requests/' + pvd_number + '/find_type_records?region=%s&section_number=%s&type=deal_record&limit=10&skip=0' % (
            self.region, kn_number)
        resp = self.request_url(url)
        dic['Сделки'] = json.loads(resp.text)['data']
        # Погашения права при отказе от права собственности на ЗУ
        url = "http://" + self.pkurp_address + '/api/requests/' + pvd_number + '/find_type_records?region=%s&section_number=%s&type=renouncement_ownership_record&limit=10&skip=0' % (
            self.region, kn_number)
        resp = self.request_url(url)
        dic['Погашения права при отказе от права собственности на ЗУ'] = json.loads(resp.text)['data']
        # Безхозяйное имущество
        url = "http://" + self.pkurp_address + '/api/requests/' + pvd_number + '/find_type_records?region=%s&section_number=%s&type=ownerless_right_record&limit=10&skip=0' % (
            self.region, kn_number)
        resp = self.request_url(url)
        dic['Безхозяйное имущество'] = json.loads(resp.text)['data']

        return dic

    def clear_restrictions_encumbrances_attributes(self, url):
        restricting_rights_attributes = {}
        restricting_rights_attributes['utf8'] = u'\u2713'
        restricting_rights_attributes['_method'] = 'patch'
        restricting_rights_attributes['authenticity_token'] = self.curent_token_record
        restricting_rights_attributes['registry_data_container[cancelled]'] = 0
        restricting_rights_attributes[
            'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][id]'] = \
            self.curent_edit_record['restrictions_encumbrances_data']['_id']['$oid']
        restricting_rights_attributes['registry_data_container[data_attributes][id]'] = self.curent_edit_record['_id'][
            '$oid']
        restricting_rights_attributes[
            'registry_data_container[data_attributes][_type]'] = 'RegistryData::RestrictRecord'
        if len(self.curent_edit_record['restrictions_encumbrances_data']['restricting_rights']) != 0:
            for count in range(0, len(self.curent_edit_record['restrictions_encumbrances_data']['restricting_rights'])):
                restricting_rights_attributes[
                    'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][restricting_rights_attributes][%s][_destroy]' % count] = True
                restricting_rights_attributes[
                    'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][restricting_rights_attributes][%s][id]' % count] = \
                    self.curent_edit_record['restrictions_encumbrances_data']['restricting_rights'][count]['_id'][
                        '$oid']
                restricting_rights_attributes[
                    'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][restricting_rights_attributes][%s][_type]' % count] = \
                    self.curent_edit_record['restrictions_encumbrances_data']['restricting_rights'][count]['_type']
            post_data = restricting_rights_attributes
            resp = self.br.post(url=url, data=post_data, headers={'X-CSRF-Token': self.curent_token_record})

    def clear_restricting_rights_attributes(self, url):
        '''
        Удаляем все ограничения прав
        '''
        restricting_rights_attributes = {}
        restricting_rights_attributes['utf8'] = u'\u2713'
        restricting_rights_attributes['_method'] = 'patch'
        restricting_rights_attributes['authenticity_token'] = self.curent_token_record
        restricting_rights_attributes['registry_data_container[cancelled]'] = 0
        restricting_rights_attributes['registry_data_container[data_attributes][restrict_parties_attributes][id]'] = \
            self.curent_edit_record['restrict_parties']['_id']['$oid']
        restricting_rights_attributes['registry_data_container[data_attributes][id]'] = self.curent_edit_record['_id'][
            '$oid']
        restricting_rights_attributes[
            'registry_data_container[data_attributes][_type]'] = 'RegistryData::RestrictRecord'
        if len(self.curent_edit_record['restrict_parties']['restricting_rights_parties']) != 0:
            # print(len(self.curent_edit_record['restrict_parties']['restricting_rights_parties']))
            for count in range(0, len(self.curent_edit_record['restrict_parties']['restricting_rights_parties'])):
                restricting_rights_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][_destroy]' % count] = 'true'
                restricting_rights_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][_type]' % count] = 'RegistryData::RestrictingRightsParty'
                restricting_rights_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][id]' % count] = \
                    self.curent_edit_record['restrict_parties']['restricting_rights_parties'][count]['_id']['$oid']

            post_data = restricting_rights_attributes
            resp = self.br.post(url=url, data=post_data, headers={'X-CSRF-Token': self.curent_token_record,
                                                                  'X-Requested-With': 'XMLHttpRequest'})

    def get_restricting_rights_attributes_by_kn(self, kn_number, path_url):
        '''
        Просматриваем
        Редактируем запись
        Общие сведения об ограничениях и обременениях - Ограничиваемые права - Номер реестровой записи о вещном праве
        Для выбираем из доступных записей те у которых кадастровый номер и ФИО собственника совпадает и № регистрационный такой же как в постановление. Если таких нет, то накладываем арест на всех. И добавляем их
        Если не долевое добавляем  все записи где КН совпадает, она должна быть одна...
        '''
        # http://pkurp-app-balancer-01.prod.egrn/11/requests/PKPVD-2019-01-18-123165/registry_data_containers/statements/PKPVD-2019-01-18-123165-11-01/possible_law_links?link_type=right_record
        url = "http://" + self.pkurp_address + path_url.split('/containers')[
            0] + '/possible_law_links?link_type=right_record'
        # print(url)
        resp = self.request_url(url)
        s = BeautifulSoup(resp.text, 'lxml')
        tr_cells = s.findAll('tr')
        restricting_rights_attributes = {}
        count = 0
        for tr in tr_cells:
            l = []
            # print(tr)
            # print(tr.findNext('td').findNext('td').findNext('td').text)
            if tr.findNext('td').findNext('td').findNext('td').text == kn_number:
                debtorname_from_fgis = tr.findNext('td').findNext('td').findNext('td').findNext('td').findNext(
                    'td').text.lower()
                debtorname_from_xml = self.xml_soup.find('debtorname').text.encode('iso-8859-1').decode().lower()
                for reg_num in self.get_reg_num_from_xml_by_kn(kn_number):
                    if reg_num == json.loads(tr.findNext('input')['data-fields'])[
                        'right_number'] and not self.simple_arest and debtorname_from_fgis == debtorname_from_xml:
                        restricting_rights_attributes[
                            'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][restricting_rights_attributes][%s][_type]' % count] = 'RegistryData::RightRecordNumber'
                        restricting_rights_attributes[
                            'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][restricting_rights_attributes][%s][number]' % count] = \
                            json.loads(tr.findNext('input')['data-fields'])['number']
                        restricting_rights_attributes[
                            'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][restricting_rights_attributes][%s][right_number]' % count] = \
                            json.loads(tr.findNext('input')['data-fields'])['right_number']
                        count += 1
        # if (count>0):
        #	print('Zapret dolua',self.pvd_number)
        if (count == 0):
            for tr in tr_cells:
                l = []
                # print(tr)
                # print(tr.findNext('td').findNext('td').findNext('td').text)
                if tr.findNext('td').findNext('td').findNext('td').text == kn_number:
                    restricting_rights_attributes[
                        'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][restricting_rights_attributes][%s][_type]' % count] = 'RegistryData::RightRecordNumber'
                    restricting_rights_attributes[
                        'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][restricting_rights_attributes][%s][number]' % count] = \
                        json.loads(tr.findNext('input')['data-fields'])['number']
                    restricting_rights_attributes[
                        'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][restricting_rights_attributes][%s][right_number]' % count] = \
                        json.loads(tr.findNext('input')['data-fields'])['right_number']
                    count += 1
        return restricting_rights_attributes

    def get_subject_attributes(self, kn_number, path_url):
        for rec in self.registry_records_list:
            object_info = self.get_info_for_object_in_egrn(rec['cad_number'], self.pvd_number)
            for rec_right in object_info['Права']:
                if rec_right['type'] != 'Собственность':
                    self.simple_arest = False
                    break
                else:
                    self.simple_arest = True

        url = "http://" + self.pkurp_address + '/api/requests/' + self.pvd_number + '/find_type_records?region=%s&section_number=%s&type=right_record&limit=1000&skip=0' % (
            self.region, kn_number)
        # print(url)
        resp = self.request_url(url)
        # print (json.loads(resp.text)['data'])
        rights_rec = {}
        debtortype = self.xml_soup.find('debtortype').text.encode('iso-8859-1').decode()
        debtorname = self.xml_soup.find('debtorname').text.encode('iso-8859-1').decode().lower().strip()
        # print(debtorname)
        if self.xml_soup.find('debtorinn'):
            debtorinn = self.xml_soup.find('debtorinn').text.encode('iso-8859-1').decode()
        else:
            debtorinn = False
        if self.xml_soup.find('debtorogrn'):
            debtorogrn = self.xml_soup.find('debtorogrn').text.encode('iso-8859-1').decode()
        else:
            debtorogrn = False
        right_record_json = json.loads(resp.text)['data']
        indolya = False
        for rec in right_record_json:
            if self.simple_arest:
                # print('wad')
                if rec['status'] == 'Актуальная':  # and subject_name in rec['right_holders']
                    rights_rec[rec['record_number']] = rec
            else:
                url = "http://" + self.pkurp_address + "/search/items/record?number=%s" % rec['record_number']
                resp = self.request_url(url)
                s = BeautifulSoup(resp.text, 'lxml')
                right = json.loads(s.find('div', {'class': 'react-form'})['data-data'])
                for count in range(0, len(right['right_holders'])):
                    if right['right_holders'][count]['_type'] == 'RegistryData::Individual':
                        # print(rec['right_holders'].lower())
                        # print(debtorname)
                        if debtorname in rec['right_holders'].lower().strip():
                            # print('1')
                            indolya = True
                        elif debtorinn == right['right_holders'][count]['inn']:
                            # print('2')
                            indolya = True
                        elif right['right_holders'][count].get('ogrn', ):
                            # print('3')
                            if debtorogrn == right['right_holders'][count]['ogrn']:
                                indolya = True
                        else:
                            indolya = False
                    else:
                        # print(rec['right_holders'].lower())
                        # print(debtorname)
                        if debtorname in rec['right_holders'].lower().strip():
                            indolya = True
                        elif right['right_holders'][count].get('entity', ):
                            if right['right_holders'][count]['entity'].get('inn', ):
                                if debtorinn == right['right_holders'][count]['entity']['inn']:
                                    indolya = True
                            elif right['right_holders'][count]['entity'].get('ogrn', ):
                                if debtorogrn == right['right_holders'][count]['entity']['ogrn']:
                                    indolya = True
                        else:
                            indolya = False
                    if indolya:
                        rights_rec[rec['record_number']] = rec
        if len(rights_rec) == 0:
            # print(len(rights_rec))
            for rec in right_record_json:
                if rec['status'] == 'Актуальная':  # and subject_name in rec['right_holders']
                    rights_rec[rec['record_number']] = rec
        # print(indolya)
        # print (rights_rec)
        count = 1
        subject_attributes = {}
        # print(rights_rec)
        for key in rights_rec.keys():
            url = "http://" + self.pkurp_address + "/search/items/record?number=%s" % key
            resp = self.request_url(url)
            s = BeautifulSoup(resp.text, 'lxml')
            right = json.loads(s.find('div', {'class': 'react-form'})['data-data'])

            subject_attributes[
                'registry_data_container[data_attributes][restrict_parties_attributes][restricted_rights_parties_attributes][0][_type]'] = 'RegistryData::RestrictedRightsParty'
            subject_attributes[
                'registry_data_container[data_attributes][restrict_parties_attributes][restricted_rights_parties_attributes][0][subject_attributes][_type]'] = 'RegistryData::Dyn::RestrictedRightsParty::Subject::Undefined'
            subject_attributes[
                'registry_data_container[data_attributes][restrict_parties_attributes][restricted_rights_parties_attributes][0][subject_attributes][undefined]'] = 'Не определено'
            subject_attributes[
                'registry_data_container[data_attributes][restrict_parties_attributes][restricted_rights_parties_attributes][0][type][value]'] = 'Не определено'
            if right['right_holders'][count - 1]['_type'] == 'RegistryData::Individual':
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][_type]' % count] = 'RegistryData::RestrictedRightsParty'
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][_type]' % count] = \
                    right['right_holders'][count - 1]['_type']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][birth_date]' % count] = \
                    right['right_holders'][count - 1]['birth_date']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][birth_place]' % count] = \
                    right['right_holders'][count - 1]['birth_place']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][citizenship_attributes][_type]' % count] = \
                    right['right_holders'][count - 1]['citizenship']['_type']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][citizenship_attributes][citizenship_country][value]' % count] = \
                    right['right_holders'][count - 1]['citizenship']['citizenship_country']['value']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][comment]' % count] = \
                    right['right_holders'][count - 1].get('comment', None)
                if right['right_holders'][count - 1].get('contacts', None):
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes][_type]' % count] = \
                        right['right_holders'][count - 1]['contacts']['_type']
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes][email]' % count] = \
                        right['right_holders'][count - 1]['contacts']['email']
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes][mailing_addess]' % count] = \
                        right['right_holders'][count - 1]['contacts']['mailing_addess']
                    if right['right_holders'][count - 1]['contacts']['old_addresses'] == None:
                        subject_attributes[
                            'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes][old_addresses_attributes]' % count] = None
                    else:
                        subject_attributes[
                            'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes][old_addresses_attributes][_type]' % count] = \
                            right['right_holders'][count - 1]['contacts']['old_addresses']['_type']
                        subject_attributes[
                            'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes][old_addresses_attributes][another_address]' % count] = \
                            right['right_holders'][count - 1]['contacts']['old_addresses']['another_address']
                        subject_attributes[
                            'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes][old_addresses_attributes][another_organ_address]' % count] = \
                            right['right_holders'][count - 1]['contacts']['old_addresses']['another_organ_address']
                        subject_attributes[
                            'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes][old_addresses_attributes][executive_organ_address]' % count] = \
                            right['right_holders'][count - 1]['contacts']['old_addresses']['executive_organ_address']
                        subject_attributes[
                            'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes][old_addresses_attributes][fact_address]' % count] = \
                            right['right_holders'][count - 1]['contacts']['old_addresses']['fact_address']
                        subject_attributes[
                            'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes][old_addresses_attributes][registry_address]' % count] = \
                            right['right_holders'][count - 1]['contacts']['old_addresses']['registry_address']
                else:
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes]' % count] = None

                # print(right['right_holders'])
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][identity_doc_attributes][_type]' % count] = \
                    right['right_holders'][count - 1]['identity_doc']['_type']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][identity_doc_attributes][additional_information]' % count] = \
                    right['right_holders'][count - 1]['identity_doc']['additional_information']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][identity_doc_attributes][civil_number]' % count] = \
                    right['right_holders'][count - 1]['identity_doc']['civil_number']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][identity_doc_attributes][doc_source]' % count] = \
                    right['right_holders'][count - 1]['identity_doc']['doc_source']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][identity_doc_attributes][document_code][value]' % count] = \
                    right['right_holders'][count - 1]['identity_doc']['document_code']['value']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][identity_doc_attributes][document_date]' % count] = \
                    right['right_holders'][count - 1]['identity_doc']['document_date']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][identity_doc_attributes][document_info]' % count] = \
                    right['right_holders'][count - 1]['identity_doc']['document_info']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][identity_doc_attributes][document_issuer]' % count] = \
                    right['right_holders'][count - 1]['identity_doc']['document_issuer']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][identity_doc_attributes][document_name]' % count] = \
                    right['right_holders'][count - 1]['identity_doc']['document_code']['value']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][identity_doc_attributes][document_number]' % count] = \
                    right['right_holders'][count - 1]['identity_doc']['document_number']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][identity_doc_attributes][document_series]' % count] = \
                    right['right_holders'][count - 1]['identity_doc']['document_series']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][identity_doc_attributes][document_start_date]' % count] = \
                    right['right_holders'][count - 1]['identity_doc']['document_start_date']
                if right['right_holders'][count - 1]['identity_doc']['migration_id'] == None:
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][identity_doc_attributes][migration_id_attributes]' % count] = None
                else:
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][identity_doc_attributes][migration_id_attributes][_type]' % count] = \
                        right['right_holders'][count - 1]['identity_doc']['migration_id']['_type']
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][identity_doc_attributes][migration_id_attributes][doc_uis_id]' % count] = \
                        right['right_holders'][count - 1]['identity_doc']['migration_id']['doc_uis_id']

                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][identity_doc_attributes][special_marks]' % count] = \
                    right['right_holders'][count - 1]['identity_doc']['special_marks']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][identity_doc_attributes][subdivision_code]' % count] = \
                    right['right_holders'][count - 1]['identity_doc']['subdivision_code']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][individual_type][value]' % count] = \
                    right['right_holders'][count - 1]['individual_type']['value']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][inn]' % count] = \
                    right['right_holders'][count - 1]['inn']
                if right['right_holders'][count - 1]['migration_id'] == None:
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][migration_id_attributes]' % count] = None
                else:
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][migration_id_attributes][_type]' % count] = \
                        right['right_holders'][count - 1]['migration_id']['_type']
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][migration_id_attributes][subject_uis_id]' % count] = \
                        right['right_holders'][count - 1]['migration_id']['subject_uis_id']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][name]' % count] = \
                    right['right_holders'][count - 1]['name']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][patronymic]' % count] = \
                    right['right_holders'][count - 1]['patronymic']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][snils]' % count] = \
                    right['right_holders'][count - 1]['snils']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][surname]' % count] = \
                    right['right_holders'][count - 1]['surname']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][type][value]' % count] = 'Правообладатель'
            else:
                # print(right['right_holders'][count-1])
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][_type]' % count] = 'RegistryData::RestrictedRightsParty'
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][_type]' % count] = \
                    right['right_holders'][count - 1]['_type']
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][comment]' % count] = \
                    right['right_holders'][count - 1].get('comment', None)
                if right['right_holders'][count - 1].get('contacts', None):
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes][_type]' % count] = \
                        right['right_holders'][count - 1]['contacts']['_type']
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes][email]' % count] = \
                        right['right_holders'][count - 1]['contacts']['email']
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes][mailing_addess]' % count] = \
                        right['right_holders'][count - 1]['contacts']['mailing_addess']
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes][old_addresses_attributes][_type]' % count] = \
                        right['right_holders'][count - 1]['contacts']['old_addresses']['_type']
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes][old_addresses_attributes][another_address]' % count] = \
                        right['right_holders'][count - 1]['contacts']['old_addresses']['another_address']
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes][old_addresses_attributes][another_organ_address]' % count] = \
                        right['right_holders'][count - 1]['contacts']['old_addresses']['another_organ_address']
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes][old_addresses_attributes][executive_organ_address]' % count] = \
                        right['right_holders'][count - 1]['contacts']['old_addresses']['executive_organ_address']
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes][old_addresses_attributes][fact_address]' % count] = \
                        right['right_holders'][count - 1]['contacts']['old_addresses']['fact_address']
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes][old_addresses_attributes][registry_address]' % count] = \
                        right['right_holders'][count - 1]['contacts']['old_addresses']['registry_address']
                else:
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][contacts_attributes]' % count] = None
                if right['right_holders'][count - 1].get('entity', None):
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][entity_attributes][_type]' % count] = \
                        right['right_holders'][count - 1]['entity']['_type']
                    if right['right_holders'][count - 1]['entity'].get('incorporation_form', None):
                        subject_attributes[
                            'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][entity_attributes][incorporation_form][value]' % count] = \
                            right['right_holders'][count - 1]['entity']['incorporation_form']['value']
                    else:
                        subject_attributes[
                            'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][entity_attributes][incorporation_form]' % count] = None
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][entity_attributes][inn]' % count] = \
                        right['right_holders'][count - 1]['entity']['inn']
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][entity_attributes][kpp]' % count] = \
                        right['right_holders'][count - 1]['entity']['kpp']

                    if right['right_holders'][count - 1]['entity'].get('name', None):
                        subject_attributes[
                            'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][entity_attributes][name]' % count] = \
                            right['right_holders'][count - 1]['entity']['name']
                    else:
                        subject_attributes[
                            'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][entity_attributes][name]' % count] = None

                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][entity_attributes][ogrn]' % count] = \
                        right['right_holders'][count - 1]['entity']['ogrn']
                else:
                    right['right_holders'][count - 1]['entity'] = None
                if right['right_holders'][count - 1].get('migration_id', None):
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][migration_id_attributes][_type]' % count] = \
                        right['right_holders'][count - 1]['migration_id']['_type']
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][migration_id_attributes][subject_uis_id]' % count] = \
                        right['right_holders'][count - 1]['migration_id']['subject_uis_id']
                else:
                    right['right_holders'][count - 1]['migration_id'] = None
                if right['right_holders'][count - 1].get('type', None):
                    subject_attributes[
                        'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][subject_attributes][type][value]' % count] = \
                        right['right_holders'][count - 1]['type']['value']
                else:
                    right['right_holders'][count - 1]['type'] = None
                subject_attributes[
                    'registry_data_container[data_attributes][restrict_parties_attributes][restricting_rights_parties_attributes][%s][type][value]' % count] = 'Правообладатель'

            # print(subject_attributes)
            return subject_attributes

    def get_name_document(self, code):
        '''
        Название документ по словарю для кода
        '''
        return dict_doc_name[code]

    def get_dolya_from_xml_by_kn(self, kn):
        '''
        Размер доли указанный в ХМЛ для кадастрового номера
        '''
        internalkey = []
        dolya_list = []
        s = None
        for svednedvdata in self.xml_soup.findAll('svednedvdata'):
            if svednedvdata.find('kadastrn').text == kn:
                internalkey.append(svednedvdata.find('internalkey').text)
        if len(internalkey) > 0:
            for svednedvrightdata in self.xml_soup.findAll('svednedvrightdata'):
                if svednedvrightdata.find('ownerinternalkey').text in internalkey:
                    if svednedvrightdata.find('sharetext'):
                        dolya_list.append(svednedvrightdata.find('sharetext').text.encode('iso-8859-1').decode())

        if len(dolya_list) > 0:
            if len(dolya_list) == 1:
                s = ' на %s доли' % dolya_list[0]
            else:
                s = ' на %s ' % dolya_list[0]
                for i in range(1, len(dolya_list)):
                    s += ' и ' + dolya_list[i]
                s += ' долю'
        else:
            s = None
        return '' if s is None else str(s)

    def get_reg_num_from_xml_by_kn(self, kn):
        '''
        Возвращает номер регистрации права из ХМЛ для кадастрового номера
        '''
        internalkey = []
        regnumber_list = []
        for svednedvdata in self.xml_soup.findAll('svednedvdata'):
            if svednedvdata.find('kadastrn').text == kn:
                # internalkey=svednedvdata.find('internalkey').text
                internalkey.append(svednedvdata.find('internalkey').text)
        # print(internalkey)
        for svednedvrightdata in self.xml_soup.findAll('svednedvrightdata'):
            if svednedvrightdata.find('ownerinternalkey').text in internalkey:
                if svednedvrightdata.find('regnumber'):
                    regnumber_list.append(svednedvrightdata.find('regnumber').text.encode('iso-8859-1').decode())
            # return
        # else:
        # return ''
        if len(regnumber_list) > 0:
            return regnumber_list
        else:
            return ''

    def underlying_documents_attributes(self, kn):
        '''
        Заполняем документ основание
        '''
        url = "http://" + self.pkurp_address + self.curent_edit_record_zayv_path
        # print(url)
        resp = self.request_url(url)
        s = BeautifulSoup(resp.text, 'lxml')
        # print(s.find('ns2:name').findNext('ns2:name').text)
        underlying_document = {}
        if s.find('ns2:issuedate'):
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][_type]'] = {
                'RegistryData::DocumentRequisites'}
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][additional_information]'] = None
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][civil_number]'] = None
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][doc_source]'] = None
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][document_code][value]'] = 'Постановление судебного пристава-исполнителя'
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][document_date]'] = s.find(
                'ns2:issuedate').text
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][document_info]'] = None
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][document_issuer]'] = s.find(
                'ns2:name').findNext('ns2:name').text
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][document_name]'] = s.find(
                'ns2:name').text
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][document_number]'] = s.find(
                'ns2:number').text
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][document_series]'] = None
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][document_start_date]'] = None
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][special_marks]'] = s.find(
                'ns3:text').text.replace('Постановление о', 'О')
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][subdivision_code]'] = None
        else:
            s = self.xml_soup
            # s.find('doccode').text
            if self.get_name_document(
                    s.find('doccode').text) == 'Постановление о снятии запрета на совершение действий по регистрации':
                naimenovanie = 'о снятии запрета'
            elif self.get_name_document(
                    s.find('doccode').text) == 'Постановление о запрете на совершение действий по регистрации':
                naimenovanie = 'о запрете'
            else:
                naimenovanie = s.find('doccode').text.encode('iso-8859-1').decode()
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][_type]'] = {
                'RegistryData::DocumentRequisites'}
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][additional_information]'] = None
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][civil_number]'] = None
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][doc_source]'] = None
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][document_code][value]'] = 'Постановление судебного пристава-исполнителя'
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][document_date]'] = s.find(
                'docdate').text
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][document_info]'] = None
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][document_issuer]'] = s.find(
                'ospname').text.encode('iso-8859-1').decode()
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][document_name]'] = u"Постановление судебного пристава-исполнителя({0}) {1}".format(
                s.find('spifio').text.encode('iso-8859-1').decode(), naimenovanie) + self.get_dolya_from_xml_by_kn(kn)
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][document_number]'] = s.find(
                'docnum').text
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][document_series]'] = None
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][document_start_date]'] = None
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][special_marks]'] = self.get_name_document(
                s.find('doccode').text).replace('Постановление о', 'О') + " (" + s.find('ipnum').text.encode(
                'iso-8859-1').decode() + ")" + self.get_dolya_from_xml_by_kn(kn)
            underlying_document[
                'registry_data_container[data_attributes][underlying_documents_attributes][0][subdivision_code]'] = None
        return underlying_document

    def spisok_proverok_result(self, pvd_number, iteration):
        # Проверка успешности проверок
        return_result = False
        print(f'{time.ctime()}')
        print('Проверка проверок: ', pvd_number, ' итерация: ', iteration)
        iteration = iteration + 1
        url = "http://" + self.pkurp_address + "/00/requests/%s/registry_data_containers/registry_data_validation_results" % pvd_number
        # print(url)
        validate_result = self.request_url(url)
        # validate_result = self.br.get(
        #     "http://" + self.pkurp_address + "/00/requests/%s/registry_data_containers/registry_data_validation_results"
        #     % pvd_number)
        json_validate_result = json.loads(validate_result.text)
        validate = {}
        if json_validate_result['validations_status'] == 'done':
            s = BeautifulSoup(json_validate_result['html'], 'lxml')
            div_result = s.find('div', {'class': 'validation-results'})
            divs = div_result.findAll('div', {}, False)
            current_validate_name = ''
            for div in divs:
                validate_title = div.find('h5')
                if validate_title is None:
                    result = div.find('div', {'class': 'empty-fill'})
                    if result is None:
                        validate[current_validate_name] = 'uncheck'
                    else:
                        validate[current_validate_name] = 'checked'
                else:
                    current_validate_name = validate_title.text
                    validate[validate_title.text] = 'uncheck'
                # validate_item = {validate_title.text: 'uncheck'}
                # validate.append(validate_item)

            # success_result = s.findAll('div', {'class': 'empty-fill'})
            # if json_validate_result['validations_status'] == 'done' and len(success_result) >= 3:

            # return True
            if validate.get('Проверка обязательности атрибутов') is None or validate.get(
                    'Проверка корректности атрибутов') is None:
                if iteration < 10:
                    print('5_0) пустой список проверок, через 30сек. повторно проверим')
                    print()
                    # iteration = iteration + 1
                    time.sleep(30)
                    return_result = self.spisok_proverok_result(pvd_number, iteration)
                    # try:
                    #     self.spisok_proverok_result(pvd_number, iteration)
                    # except Exception as e:
                    #     print(str(e))
            elif validate['Проверка обязательности атрибутов'] == 'checked' and validate[
                'Проверка корректности атрибутов'] == 'checked':
                return True
            else:
                return False
        else:
            if iteration < 10:
                print('5_0) проверки не прошли, через 30сек. повторно проверим завешение проверок.')
                print()
                # iteration = iteration + 1
                time.sleep(30)
                return_result = self.spisok_proverok_result(pvd_number, iteration)
                # try:
                #     self.spisok_proverok_result(pvd_number, iteration)
                # except Exception as e:
                #     print(str(e))
            else:
                return False

        return return_result

    def compleate_encumbrance(self, pvd_number):
        '''
        Завершить обработку и передать на следующую стадию
        '''
        print('Проверка прохождения проверок перед передачей на следующую стадию')
        if self.spisok_proverok_result(pvd_number, 0):
            # http://pkurp-app-balancer-01.prod.egrn/11/requests/PKPVD-2019-04-02-063355/validations/complete
            self.br.post(url="http://" + self.pkurp_address + "/00/requests/%s/validations/complete" % pvd_number,
                         headers={'X-CSRF-Token': self.curent_token_record})
            # print('action')
            return True
        else:
            return 'FAIL_VALIDATION'

    def compleate_arest(self, pvd_number):
        '''
        Завершить обработку и передать на следующую стадию
        '''
        if json.loads(self.br.get(
                "http://" + self.pkurp_address + "/00/requests/%s/registry_data_containers/registry_data_validation_results" % pvd_number).text)[
            'validations_status'] == 'done':
            # http://pkurp-app-balancer-01.prod.egrn/11/requests/PKPVD-2019-04-02-063355/validations/complete
            self.br.post(url="http://" + self.pkurp_address + "/00/requests/%s/validations/complete" % pvd_number,
                         headers={'X-CSRF-Token': self.curent_token_record})
            # print('action')
            return True
        else:
            return 'FAIL_VALIDATION'

    # print('FAIL_VALIDATION',pvd_number)
    def refresh_registry_records(self):
        # обновить сведения егрн
        url = "http://" + self.pkurp_address + '/api/requests/' + '%s/registry_records?region=00&limit=1000&skip=0' % self.pvd_number
        # print(url)
        resp = self.request_url(url)
        # print(resp.text)
        registry_records = {}
        registry_rec = json.loads(resp.text)['data']
        for rec in self.registry_records_list:
            # print(rec)
            url = "http://" + self.pkurp_address + '/%s/requests/' % self.region + self.pvd_number + '/registry_records/' + \
                  rec['_id']['$oid'] + '/refresh'
            resp = self.request_url(url)

    def extinguish_encumbrance(self, record_number):
        # функция отправляет запрос на погашение обременения по регистрационному номеру
        url = "http://" + self.pkurp_address + '/%s/requests/' % self.region + self.pvd_number + '/registry_data_containers/statements/' + self.pvd_number + '-%s-01/containers' % self.region
        # print(url)
        post_data = {'utf8': u'\u2713',
                     'authenticity_token': self.curent_token_record,
                     'registry_data[type]': 'change_record',
                     'registry_data[record_number]': record_number,
                     'registry_data[cancelled]': True}
        # print('Post data: ', post_data)
        resp = self.br.post(url, data=post_data)
        return resp

    def change_reference_document(self, docs, current_edit_record,
                                  current_token_record_edit,
                                  underlying_documents_id,
                                  edit_path, subject):
        # изменение документа основания
        # yesterday = time.strftime('%d.%m.%Y', time.gmtime(time.time() - 86400))
        post_data = {
            '_method': 'patch',
            'authenticity_token': current_token_record_edit,
            'registry_data_container[cancelled]': '1',
            'registry_data_container[data_attributes][id]': current_edit_record['_id']['$oid'],
            'registry_data_container[data_attributes][_type]': 'RegistryData::RestrictRecord',
            # 'registry_data_container[underlying_documents_holder_attributes][underlying_documents_attributes][0][document_code][value]': 'Заявление о погашении регистрационной записи об ипотеке (статья 53 Закона, статья 25 Федерального закона от 16 июля 1998 г. N 102-ФЗ "Об ипотеке (залоге недвижимости)"',
            # 'registry_data_container[underlying_documents_holder_attributes][underlying_documents_attributes][0][document_name]': u"Заявление {0} о погашение регистрационной записи об ипотеке".format(
            #     subject),
            # 'registry_data_container[underlying_documents_holder_attributes][underlying_documents_attributes][0][document_number]': document_number,
            # 'registry_data_container[underlying_documents_holder_attributes][underlying_documents_attributes][0][document_date]': document_date,
            # 'registry_data_container[underlying_documents_holder_attributes][underlying_documents_attributes][0][_type]': 'RegistryData::DocumentRequisites',
            'registry_data_container[underlying_documents_holder_attributes][id]': underlying_documents_id,
            'registry_data_container[underlying_documents_holder_attributes][_type]': 'RegistryData::UnderlyingDocumentsHolder'
        }
        key = 0
        for doc_item in docs:
            post_data[
                'registry_data_container[underlying_documents_holder_attributes][underlying_documents_attributes][%s][document_code][value]' % key] = \
            doc_item['doc_code']
            post_data[
                'registry_data_container[underlying_documents_holder_attributes][underlying_documents_attributes][%s][document_name]' % key] = \
            doc_item['doc_name']
            post_data[
                'registry_data_container[underlying_documents_holder_attributes][underlying_documents_attributes][%s][document_number]' % key] = \
            doc_item['doc_number']
            post_data[
                'registry_data_container[underlying_documents_holder_attributes][underlying_documents_attributes][%s][document_date]' % key] = \
            doc_item['doc_date']
            post_data[
                'registry_data_container[underlying_documents_holder_attributes][underlying_documents_attributes][%s][_type]' % key] = 'RegistryData::DocumentRequisites'
            key = key + 1

        # http://pkurp-app-balancer-01.prod.egrn/11/requests/Other-2019-04-10-012986/registry_data_containers/statements/Other-2019-04-10-012986-11-01/containers/5caddc799936e8292526b430
        url = "http://" + self.pkurp_address + edit_path
        # print(url)
        # post_data.update(underlying_document)
        # print(post_data)
        # погасить!!!!
        resp = self.br.post(url, data=post_data, headers={'X-CSRF-Token': self.curent_token_record})
        return resp

    def sniatie_arest(self):
        # print('sniatie',pkpvd_number)
        # обновить сведения егрн
        self.refresh_registry_records()
        # удалить все сформированные сведения
        # self.get_registry_data_container_records(pkpvd_number)

        # print(pkpvd_number)
        for key in self.registry_records.keys():
            url = "http://" + self.pkurp_address + self.registry_records[key][2].replace('/edit', '')
            post_data = {
                '_method': 'delete',
                'authenticity_token': self.curent_token_record}
            resp = self.br.post(url, data=post_data)
        # открыть сведения егрн и поискать арест
        ipnum = self.xml_soup.find('ipnum').text.encode('iso-8859-1').decode()
        restrdocnumber = self.xml_soup.find('restrdocnumber').text.encode('iso-8859-1').decode()
        count_sniatie = 0
        # переберем все объекты

        for rec in self.registry_records_list:
            # url="http://"+self.pkurp_address+'/api/requests/'+'%s/find_type_records?region=11&section_number=%s&type=restrict_record&limit=10&skip=0'%(self.pvd_number,rec['cad_number'])
            # print(url)
            # resp=self.request_url(url)
            # в них все аресты
            for rec_restrict in self.get_right_record_list(rec['cad_number']):
                url = "http://" + self.pkurp_address + '/%s/requests/' % self.region + self.pvd_number + '/registry_records/' + \
                      rec_restrict['_id']['$oid']
                resp_2 = self.request_url(url)
                s = BeautifulSoup(resp_2.text, 'lxml')
                restrict = json.loads(s.find('div', {'class': 'react-form'})['data-data'])
                # print(url)
                sniatie_true = False
                # print(restrict['underlying_documents'])
                for i in range(0, len(restrict['underlying_documents'])):
                    # print(restrict['underlying_documents'][i])
                    if restrict['underlying_documents'][i]['document_number']:
                        if restrdocnumber:
                            if restrdocnumber.lower() in restrict['underlying_documents'][i]['document_number'].lower():
                                sniatie_true = True
                    if restrict['underlying_documents'][i]['special_marks']:
                        # print(ipnum.lower())
                        # print(restrict['underlying_documents'][i]['special_marks'].lower())
                        if ipnum.lower() in restrict['underlying_documents'][i]['special_marks'].lower():
                            sniatie_true = True
                    if restrict['underlying_documents'][i]['document_info']:
                        if ipnum.lower() in restrict['underlying_documents'][i]['document_info'].lower():
                            sniatie_true = True
                # print(restrict['underlying_documents'][i]['special_marks'].lower())
                # print(ipnum.lower())
                if sniatie_true:
                    count_sniatie += 1
                    # print(rec_restrict['record_number'])
                    url = "http://" + self.pkurp_address + '/%s/requests/' % self.region + self.pvd_number + '/registry_data_containers/statements/' + self.pvd_number + '-%s-01/containers' % self.region
                    # print(url)
                    post_data = {'utf8': u'\u2713',
                                 'registry_data[cancelled]': True,
                                 'registry_data[record_number]': rec_restrict['record_number'],
                                 'authenticity_token': self.curent_token_record,
                                 'registry_data[type]': 'change_record'}
                    resp = self.br.post(url, data=post_data)
                    # print(resp.text)
                    s = BeautifulSoup(resp.text, 'lxml')

                    # print(resp.text)
                    # self.curent_token_record=s.find('input',{'name':'authenticity_token'})['value']
                    edit_path = s.find('form', {'id': 'edit_registry_data_container'})['action']
                    underlying_documents_id = json.loads(
                        s.find('div', {'data-class-name': 'RegistryData::UnderlyingDocumentsHolder'})[
                            'data-data'].replace('&quot;', '"'))['_id']['$oid']
                    curent_token_record_edit = s.find('meta', {'name': 'csrf-token'})['content']
                    # print(self.curent_token_record)
                    self.curent_edit_record = json.loads(
                        s.find('div', {'class': 'react-form'})['data-data'].replace('&quot;', '"'))
                    self.curent_edit_record_zayv_path = s.find('a', {'class': 'js-docs-name'})['data-doc-path']
                    # underlying_document=self.underlying_documents_attributes()
                    if self.get_name_document(self.xml_soup.find(
                            'doccode').text) == 'Постановление о снятии запрета на совершение действий по регистрации':
                        naimenovanie = 'о снятии запрета'
                    elif self.get_name_document(self.xml_soup.find(
                            'doccode').text) == 'Постановление о запрете на совершение действий по регистрации':
                        naimenovanie = 'о запрете'
                    else:
                        naimenovanie = self.xml_soup.find('doccode').text.encode('iso-8859-1').decode()
                    # print(s)
                    post_data = {
                        '_method': 'patch',
                        'authenticity_token': curent_token_record_edit,
                        'registry_data_container[cancelled]': '1',
                        'registry_data_container[data_attributes][id]': self.curent_edit_record['_id']['$oid'],
                        'registry_data_container[data_attributes][_type]': 'RegistryData::RestrictRecord',
                        'registry_data_container[underlying_documents_holder_attributes][_type]': 'RegistryData::UnderlyingDocumentsHolder',
                        'registry_data_container[underlying_documents_holder_attributes][id]': underlying_documents_id,
                        'registry_data_container[underlying_documents_holder_attributes][underlying_documents_attributes][0][document_code][value]': 'Постановление судебного пристава-исполнителя',
                        'registry_data_container[underlying_documents_holder_attributes][underlying_documents_attributes][0][_type]': 'RegistryData::DocumentRequisites',
                        'registry_data_container[underlying_documents_holder_attributes][underlying_documents_attributes][0][document_date]': self.xml_soup.find(
                            'docdate').text.encode('iso-8859-1').decode(),
                        'registry_data_container[underlying_documents_holder_attributes][underlying_documents_attributes][0][document_issuer]': self.xml_soup.find(
                            'ospname').text.encode('iso-8859-1').decode(),
                        'registry_data_container[underlying_documents_holder_attributes][underlying_documents_attributes][0][document_name]': u"Постановление судебного пристава-исполнителя({0}) {1}".format(
                            self.xml_soup.find('spifio').text.encode('iso-8859-1').decode(), naimenovanie),
                        'registry_data_container[underlying_documents_holder_attributes][underlying_documents_attributes][0][document_number]': self.xml_soup.find(
                            'docnum').text,
                        'registry_data_container[underlying_documents_holder_attributes][underlying_documents_attributes][0][special_marks]': self.get_name_document(
                            self.xml_soup.find('doccode').text).replace('Постановление о',
                                                                        'О') + " (" + self.xml_soup.find(
                            'ipnum').text.encode('iso-8859-1').decode() + ")",
                        'utf8': u'\u2713',
                    }
                    # http://pkurp-app-balancer-01.prod.egrn/11/requests/Other-2019-04-10-012986/registry_data_containers/statements/Other-2019-04-10-012986-11-01/containers/5caddc799936e8292526b430
                    url = "http://" + self.pkurp_address + edit_path
                    # print(url)
                    # post_data.update(underlying_document)
                    # print(post_data)
                    # погасить!!!!
                    resp = self.br.post(url, data=post_data, headers={'X-CSRF-Token': self.curent_token_record})
            # print(resp.text)
        if count_sniatie == 0:
            url = "http://" + self.pkurp_address + '/%s/requests/' % self.region + self.pvd_number + '/comments.' + self.pvd_number + '?_id=' + self.pvd_number
            post_data = {'utf8': u'\u2713',
                         'authenticity_token': self.curent_token_record,
                         'comment[text]': u'В актуальных сведениях ЕГРН нет запрета по исп./пр.'}
            resp = self.br.post(url, data=post_data)

    def edit_tabs_react_restrictions_encumbrances_data(self, kn, path_url):
        # http://pkurp-app-balancer-01.prod.egrn/11/requests/PKPVD-2019-01-16-087698/registry_data_containers/statements/PKPVD-2019-01-16-087698-11-01/containers/5c3f4801cea6a00001c108db/edit#bs-tabs-react-restrictions_encumbrances_data
        self.get_edit_record_info(path_url)
        url = "http://" + self.pkurp_address + path_url.replace('/edit', '')
        # zapis vibratb
        self.get_property_of_container(path_url)
        self.clear_restricting_rights_attributes(url)
        self.clear_restrictions_encumbrances_attributes(url)
        # zapis=
        # print(self.property_of_container)
        # документ основание
        underlying_document = self.underlying_documents_attributes(kn)
        subject_attributes = {}
        subject_attributes = self.get_subject_attributes(kn, path_url)
        restricting_rights_attributes = self.get_restricting_rights_attributes_by_kn(
            self.property_of_container['record_info']['record_number'], path_url)
        # print(restricting_rights_attributes)
        # zapolitm
        # self.get_property_of_container()
        # print(self.property_of_container)
        # формируем запись о - Предмет ограничения/обременения
        if 'Земельный' in self.property_of_container['object']['common_data']['type']['value']:
            # self.property_of_container['dated_info']['declared_area']
            if self.property_of_container['params']['permitted_use'] == None:
                permitted_use = '"не указано"'
            else:
                permitted_use = self.property_of_container['params']['permitted_use']['permitted_use_established'][
                    'by_document']

            if self.property_of_container['params']['area'] == None:
                area = " 'не указано'"
            else:
                area = self.property_of_container['params']['area']['value']
                if area == None:
                    area = '"не указано"'
            try:
                restriction_subject = self.property_of_container['object']['common_data']['type'][
                                          'value'] + ',' + ' категория - ' + \
                                      self.property_of_container['params']['category']['type'][
                                          'value'] + ',' + permitted_use + ', расположенный по адресу - ' + \
                                      self.property_of_container['address_location']['address'][
                                          'readable_address'] + ', площадью - ' + area + ' кв.м., с кадастровым номером ' + \
                                      self.property_of_container['record_info']['record_number']
            except:
                print('Земельный - ', self.property_of_container)
        elif 'Сооружение' in self.property_of_container['object']['common_data']['type']['value']:
            if self.property_of_container['params']['base_parameter']['extension'] == None:
                extension = '\"Не указано\"'
            else:
                extension = self.property_of_container['params']['base_parameter']['extension']
            try:
                restriction_subject = self.property_of_container['object']['common_data']['type'][
                                          'value'] + ', расположенное по адресу - ' + \
                                      self.property_of_container['address_location']['address'].get('readable_address',
                                                                                                    '') + ', протяженностью - ' + extension + ' м, с кадастровым номером ' + \
                                      self.property_of_container['record_info']['record_number']
            except:
                print('Сооружение - ', self.property_of_container)

        elif 'Помещение' in self.property_of_container['object']['common_data']['type']['value']:
            if self.property_of_container['params']['area'] == None:
                area = " 'не указано'"
            else:
                area = self.property_of_container['params']['area']
                if area == None:
                    area = '"не указано"'
            # print(self.property_of_container['record_info']['record_number'])
            # print()
            try:
                restriction_subject = self.property_of_container['object']['common_data']['type'][
                                          'value'] + ', расположенное по адресу - ' + \
                                      self.property_of_container['address_room']['address']['address'].get(
                                          'readable_address',
                                          '') + ', площадью - ' + area + ' кв.м., с кадастровым номером ' + \
                                      self.property_of_container['record_info']['record_number']
            except:
                # print('test')
                print('Помещение - ', self.property_of_container)
        elif 'Объект незавершенного строительства' in self.property_of_container['object']['common_data']['type'][
            'value']:
            try:
                if self.property_of_container['params']['base_parameter'].get('area', ''):
                    area = self.property_of_container['params']['base_parameter'].get('area', '')
                elif self.property_of_container['params']['base_parameter'].get('built_up_area', ''):
                    area = self.property_of_container['params']['base_parameter'].get('built_up_area', '')
                else:
                    area = ''
                restriction_subject = self.property_of_container['object']['common_data']['type'][
                                          'value'] + ', расположенное по адресу - ' + \
                                      self.property_of_container['address_location']['address'].get('readable_address',
                                                                                                    '') + ', площадью - ' + area + ' кв.м., с кадастровым номером ' + \
                                      self.property_of_container['record_info']['record_number']
            except:
                print('Объект незавершенного строительства - ', self.property_of_container)

        else:
            # print(self.property_of_container)
            if self.property_of_container['params']['area'] == None:
                area = " 'не указано'"
            else:
                # print('other - ',self.property_of_container)
                area = self.property_of_container['params']['area']
                if area == None:
                    area = '"не указано"'
            restriction_subject = self.property_of_container['object']['common_data']['type'][
                                      'value'] + ', расположенное по адресу - ' + \
                                  self.property_of_container['address_location']['address'].get('readable_address',
                                                                                                '') + ', площадью - ' + area + ' кв.м., с кадастровым номером ' + \
                                  self.property_of_container['record_info']['record_number']

            try:

                restriction_subject = self.property_of_container['object']['common_data']['type'][
                                          'value'] + ', расположенное по адресу - ' + \
                                      self.property_of_container['address_location']['address'].get('readable_address',
                                                                                                    '') + ', площадью - ' + area + ' кв.м., с кадастровым номером ' + \
                                      self.property_of_container['record_info']['record_number']
            except:
                print('other - ', self.property_of_container)

        # print(self.curent_edit_record['restrictions_encumbrances_data']['restriction_encumbrance_number'])
        # srok ne ustanovlen
        restrict_info = self.curent_edit_record['restrictions_encumbrances_data']['additional_encumbrance_info'][
            'restrict_info'].replace('Постановление', '')
        restrict_info = underlying_document[
            'registry_data_container[data_attributes][underlying_documents_attributes][0][special_marks]']
        post_data = {
            'utf8': u'\u2713',
            '_method': 'patch',
            'authenticity_token': self.curent_token_record,
            'registry_data_container[cancelled]': '0',
            'registry_data_container[data_attributes][id]': self.curent_edit_record['_id']['$oid'],
            'registry_data_container[data_attributes][record_info_attributes][_type]':
                self.curent_edit_record['record_info']['_type'],
            'registry_data_container[data_attributes][record_info_attributes][cancel_date]':
                self.curent_edit_record['record_info']['cancel_date'],
            'registry_data_container[data_attributes][record_info_attributes][id]':
                self.curent_edit_record['record_info']['_id']['$oid'],
            'registry_data_container[data_attributes][record_info_attributes][record_number]':
                self.curent_edit_record['record_info']['record_number'],
            'registry_data_container[data_attributes][record_info_attributes][registration_date]':
                self.curent_edit_record['record_info']['registration_date'],
            'registry_data_container[data_attributes][record_info_attributes][section_number]':
                self.curent_edit_record['record_info']['section_number'],
            'registry_data_container[data_attributes][restrict_parties_attributes][_type]':
                self.curent_edit_record['restrict_parties']['_type'],
            'registry_data_container[data_attributes][restrict_parties_attributes][id]':
                self.curent_edit_record['restrict_parties']['_id']['$oid'],
            'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][_type]':
                self.curent_edit_record['restrictions_encumbrances_data']['_type'],
            # как в документе
            # 'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][additional_encumbrance_info_attributes][_type]':	self.curent_edit_record['restrictions_encumbrances_data']['additional_encumbrance_info']['_type'],
            # 'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][additional_encumbrance_info_attributes][id]':	self.curent_edit_record['restrictions_encumbrances_data']['additional_encumbrance_info']['_id']['$oid'],
            # 'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][additional_encumbrance_info_attributes][restrict_info]':	restrict_info,
            # Запрещение регистрации
            'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][additional_encumbrance_info_attributes][_type]': 'RegistryData::Dyn::RestrictRecord::RestrictionsEncumbrancesData::AdditionalEncumbranceInfo::RightProhibition',
            'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][additional_encumbrance_info_attributes][id]': None,
            'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][additional_encumbrance_info_attributes][restrict_info]': restrict_info,

            'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][cad_number]':
                self.curent_edit_record['restrictions_encumbrances_data']['cad_number'],
            'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][cancel_restriction_number]	':
                self.curent_edit_record['restrictions_encumbrances_data']['cancel_restriction_number'],
            'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][id]':
                self.curent_edit_record['restrictions_encumbrances_data']['_id']['$oid'],
            'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][period_attributes][_type]': 'RegistryData::Dyn::RestrictRecord::RestrictionsEncumbrancesData::Period::NoPeriodInfo',
            'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][period_attributes][id]': None,
            'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][period_attributes][no_period]': 'Срок действия не установлен',
            'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][restriction_encumbrance_number]':
                self.curent_edit_record['restrictions_encumbrances_data']['restriction_encumbrance_number'],
            # 'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][restriction_encumbrance_type][value]':	self.curent_edit_record['restrictions_encumbrances_data']['restriction_encumbrance_type']['value'],
            'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][restriction_encumbrance_type][value]': 'Запрещение регистрации',

            'registry_data_container[data_attributes][restrictions_encumbrances_data_attributes][restriction_subject]': restriction_subject,

        }
        if restricting_rights_attributes:
            post_data.update(restricting_rights_attributes)
        if subject_attributes:
            post_data.update(subject_attributes)
        if underlying_document:
            post_data.update(underlying_document)

        resp = self.br.post(url, data=post_data)

    # print(resp.text)

    def manual_proverki_submit(self):
        '''
        Отметить ручные проверки
        '''
        # /00/requests/PKPVD-2019-01-15-138415
        # http://pkurp-app-balancer-01.prod.egrn/11/requests/PKPVD-2019-01-23-106934/validations/statements.PKPVD-2019-01-23-106934
        url = "http://" + self.pkurp_address + '/%s/requests/' % self.region + self.pvd_number + '/validations/statements'
        # print(url)
        # url = "http://" + self.pkurp_address + '/validations/statements/%s' % self.pvd_number + '-%s-01/rules' % self.region
        # print(url)
        resp = self.request_url(url)
        s = BeautifulSoup(resp.text, 'lxml')
        # ><a class="js-iframe-trigger js-validations"
        # html.turbolinks-progress-bar body.iframe-padding div div.table-container table.table tbody
        token = s.find('meta', {'name': 'csrf-token'})['content']

        url = "http://" + self.pkurp_address + s.find('a', {'class': 'js-iframe-trigger js-validations'})[
            'data-address']
        resp = self.request_url(url)
        s = BeautifulSoup(resp.text, 'lxml')
        table = s.find('tbody')

        # s=BeautifulSoup(resp.text,'lxml')
        # print(table)
        validations_dic = {}
        for tr in table.findAll('tr'):
            # print(tr['class'])
            if tr.get('data-id', None):
                # print(tr['data-id'])
                type_valid = tr['data-id']
            else:
                title = tr.findNext('td').findNext('td').findNext('a')['title']
                action = tr.findNext('form', {'method': 'post'})['action']
                status = tr.findNext('td', {'class': 'checkStatus'}).text
                validations_dic[title] = [type_valid, action, status]
        # print(validations_dic)
        for key in validations_dic.keys():
            if key == 'Проверка полномочий заявителя на возможность обратиться с заявлением':
                post_data = {'_method': 'patch',
                             'outer_validation_result[comment]': '',
                             'outer_validation_result[result]': 'success',
                             'utf8': u'\u2713'}
            elif key == 'Проверка комплектности требующихся документов в соответствии с законодательством':
                post_data = {'_method': 'patch',
                             'outer_validation_result[comment]': '',
                             'outer_validation_result[result]': 'success',
                             'utf8': u'\u2713'}
            elif key == 'Проверка наличия в представленных в форме документов на бумажном носителе подчисток либо приписок, зачеркнутых слов и иных не оговоренных в них исправлений, в том числе документов, исполненных карандашом, имеющих серьезные повреждения, не позволяющие однозначно истолковать их содержание':
                post_data = {'_method': 'patch',
                             'outer_validation_result[comment]': '',
                             'outer_validation_result[result]': 'success',
                             'utf8': u'\u2713'}
            elif key == 'Проверка: является ли объект недвижимости, объектом недвижимости, кадастровый учет которого и (или) регистрация прав на который могут быть осуществлены':
                post_data = {'_method': 'patch',
                             'outer_validation_result[comment]': '',
                             'outer_validation_result[result]': 'success',
                             'utf8': u'\u2713'}
            else:
                post_data = {'_method': 'patch',
                             'outer_validation_result[comment]': '',
                             'outer_validation_result[result]': 'suspend',
                             'utf8': u'\u2713'}
            url_proverka = "http://" + self.pkurp_address + validations_dic[key][1]
            if validations_dic[key][2] == 'Не начата':
                self.br.post(url_proverka, data=post_data, headers={'X-CSRF-Token': token})

    def spisok_proverok_reload(self):
        '''
        Перезапустить список проверок
        в качестве параметра № ПК ПВД
        '''
        # /00/requests/PKPVD-2019-01-15-138415
        # http://pkurp-app-balancer-01.prod.egrn/00/requests/PKPVD-2019-01-15-138415/registry_data_containers/statements/run_validations
        url = "http://" + self.pkurp_address + '/00/requests/' + self.pvd_number + '/registry_data_containers/registry_data_validation_results'
        resp = self.request_url(url)
        s = BeautifulSoup(json.loads(resp.text)['html'], 'lxml')
        resp_json = json.loads(resp.text)
        if resp_json['validations_status'] == 'in_process':
            return
        token = s.find('input', {'name': 'authenticity_token'})['value']
        post_data = {'authenticity_token': token,
                     'button': '',
                     'utf8': u'\u2713'}
        url = "http://" + self.pkurp_address + '/00/requests/' + self.pvd_number + '/registry_data_containers/statements/run_validations'
        resp = self.br.post(url, data=post_data)

    def get_property_of_container(self, path_url):
        url = "http://" + self.pkurp_address + path_url.replace('/edit', '/property_of_container')
        resp = self.request_url(url)
        self.property_of_container = json.loads(json.loads(resp.text)['restriction_property'])

    def get_all_from_statements(self):
        url = "http://" + self.pkurp_address + '/%s/requests/%s/documents?_id=%s' % (
            self.region, self.pvd_number, self.pvd_number)
        resp = self.request_url(url)
        s = BeautifulSoup(resp.text, 'lxml')
        self.curent_token_record = s.find('meta', {'name': 'csrf-token'})['content']
        self.statements = []
        js_docs_elements = s.findAll('li', {'class': 'js-docs-element'})
        statement = ''
        for js_docs_element in js_docs_elements:
            # Получаем ссылки на документ
            js_doc_name = js_docs_element.find('a', {'class': 'js-docs-name'})
            doc = {'type': [], 'pdf_link': '', 'name': js_doc_name.text, 'content': ''}

            if js_docs_element.find('input', {'class': 'js-autofill-element'})['data-doc-type'] == 'generated':
                continue

            # Определяем заявление
            if 'Заявление №' in js_doc_name.text:
                document_number = js_doc_name.text.replace('Заявление №', '')
                if statement != '' and statement['document_number'] != document_number:
                    self.statements.append(statement)
                statement = {'document_number': document_number, 'name': js_doc_name.text, 'docs': []}

            # Перебор типов файлов
            docs_links = js_docs_element.find('div', {'class': 'docs-links'})
            docs_links_links = docs_links.findAll('a')
            for doc_type in docs_links_links:
                doc['type'].append(doc_type.text)
                if doc_type.text == 'PDF':
                    doc['pdf_link'] = doc_type['href']

            resp = self.br.get(url="http://" + self.pkurp_address + js_doc_name['data-doc-path'])
            s = BeautifulSoup(resp.text, 'lxml')
            doc['content'] = s

            statement['docs'].append(doc)
        if statement != '':
            self.statements.append(statement)

    def get_xml_from_doc(self):
        url = "http://" + self.pkurp_address + '/%s/requests/%s/documents?_id=%s' % (
            self.region, self.pvd_number, self.pvd_number)
        resp = self.request_url(url)
        s = BeautifulSoup(resp.text, 'lxml')
        self.curent_token_record = s.find('meta', {'name': 'csrf-token'})['content']
        js_docs_names = s.findAll('a', {'class': 'js-docs-name'})
        for js_doc_name in js_docs_names:
            if '(xml)' in js_doc_name.text:
                resp = self.br.get(url="http://" + self.pkurp_address + js_doc_name['data-doc-path'])
                s = BeautifulSoup(resp.text, 'lxml')
                self.xml_soup = s

    def get_edit_record_info(self, path_url):
        url = "http://" + self.pkurp_address + path_url
        # print(url)
        resp = self.request_url(url)
        s = BeautifulSoup(resp.text, 'lxml')
        # print(self.pvd_number)
        # print(resp.text)
        self.curent_token_record = s.find('input', {'name': 'authenticity_token'})['value']
        self.curent_edit_record = json.loads(s.find('div', {'class': 'react-form'})['data-data'].replace('&quot;', '"'))
        self.curent_edit_record_zayv_path = s.find('a', {'class': 'js-docs-name'})['data-doc-path']

    def request_url(self, url):
        iteration = 0;
        while True:
            try:
                rs = self.br.get(url)
                if rs.status_code != 200:
                    # log.info("Ошибка, Код ответа: %s", rs.status)
                    print(rs.status)
                    time.sleep(3)
                    # Попробуем снова на следующей итерации цикла
                    continue
                # Если дошли до сюда, значит ошибок не было
                return rs
            except:
                # Выводим свое сообщение плюс стек трассы
                print("Ошибка получения данных с сервера")
                print(url)
                if iteration < 10:
                    print("Повторный запрос через 10 сек.")
                    time.sleep(10)
                else:
                    break

    def get_registry_records_json(self, pvd_number):
        url = "http://" + self.pkurp_address + '/api/requests/' + '%s/registry_records?region=00&limit=1000&skip=0' % pvd_number
        # print(url)
        resp = self.request_url(url)
        # print(resp.text)
        self.registry_record_json = json.loads(resp.text)
        self.registry_records = {}
        for rec in json.loads(resp.text)['data']:
            # print(rec)
            self.registry_records[rec['cad_number']] = True

    def get_registry_token(self, pvd_number):
        # список с данными по формируемым сведениями
        # http://pkurp-app-balancer-01.egron.test/00/requests/PKPVD-2019-01-14-000207/registry_data_containers/statements
        url = "http://" + self.pkurp_address + '/00/requests/%s/registry_data_containers/statements' % pvd_number
        resp = self.request_url(url)
        s = BeautifulSoup(resp.text, 'lxml')
        token = s.find('meta', {"name": "csrf-token"})['content']
        self.registry_record_token = token

    def get_registry_data_container_records(self, pvd_number):
        # список с данными по формируемым сведениями
        # http://pkurp-app-balancer-01.egron.test/00/requests/PKPVD-2019-01-14-000207/registry_data_containers/statements
        # print(pvd_number)
        url = "http://" + self.pkurp_address + '/00/requests/%s/registry_data_containers/statements' % pvd_number
        # print(url)
        resp = self.request_url(url)
        s = BeautifulSoup(resp.text, 'lxml')
        # print(resp.text)
        if s.find('div', text="Обращение находится на обработке у пользователя с другой ролью"):
            self.curent_zayv_status_in_work = False
        else:
            self.curent_zayv_status_in_work = True

        registry_data = s.find('div', {"id": "bs-tabs-registry_data-builded_registry_data"})
        registry_records = registry_data.findAll('tr', {"class": "js-table-filter-target js-draggable"})
        self.registry_records = {}
        for tr in registry_records:
            list_rec = []
            if tr.find('a', string='Внесение сведений'):
                list_rec.append(tr['data-container'])
                list_rec.append(tr['data-statement'])
                list_rec.append(tr.find('a', string='Внесение сведений')['href'])
                self.registry_records[tr.find('td', {"class": "js-table-filter-target-source"}).text] = list_rec

    def get_restrict_record_list(self, kn_number):
        '''
        Список
        '''

        url = "http://" + self.pkurp_address + '/api/requests/' + self.pvd_number + '/find_type_records?region=%s&section_number=%s&type=restrict_record&limit=1000&skip=0' % (
            self.region, kn_number)

        resp = self.request_url(url)
        count = json.loads(resp.text)['count']
        # print(count)
        restrict_record = []
        skip = 0
        while (count > skip):
            url = "http://" + self.pkurp_address + '/api/requests/' + self.pvd_number + '/find_type_records?region=%s&section_number=%s&type=restrict_record&limit=1000&skip=%s' % (
                self.region, kn_number, skip)
            # print(url)
            skip += 100
            resp = self.request_url(url)
            for rec in json.loads(resp.text)['data']:
                restrict_record.append(rec)
        return restrict_record

    def get_right_record_list(self, kn_number):
        '''
        Список
        '''

        url = "http://" + self.pkurp_address + '/api/requests/' + self.pvd_number + '/find_type_records?region=%s&section_number=%s&type=restrict_record&limit=1000&skip=0' % (
            self.region, kn_number)

        resp = self.request_url(url)
        count = json.loads(resp.text)['count']
        # print(count)
        right_records = []
        skip = 0
        while (count > skip):
            url = "http://" + self.pkurp_address + '/api/requests/' + self.pvd_number + '/find_type_records?region=%s&section_number=%s&type=restrict_record&limit=1000&skip=%s' % (
                self.region, kn_number, skip)
            # print(url)
            skip += 100
            resp = self.request_url(url)
            for rec in json.loads(resp.text)['data']:
                right_records.append(rec)
        return right_records

    def get_registry_records_list(self):
        '''
        Список кадастровых номеров в отношение которых формируются записи - Сведения ЕГРН
        '''
        url = 'http://%s/api/requests/%s/registry_records?region=00&limit=100&skip=0' % (
            self.pkurp_address, self.pvd_number)
        resp = self.request_url(url)
        count = json.loads(resp.text)['count']
        # print(count)
        registry_records = []
        skip = 0
        while (count > skip):
            url = 'http://%s/api/requests/%s/registry_records?region=00&limit=100&skip=%s' % (
                self.pkurp_address, self.pvd_number, skip)
            # print(url)
            skip += 100
            resp = self.request_url(url)
            for rec in json.loads(resp.text)['data']:
                registry_records.append(rec)
        self.registry_records_list = registry_records

    def init_module(self, module, user_name, password):
        # if not self.br:
        #	self.br = requests.Session()
        #	self.br.headers.update({'User-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/66.0.3359.139 Chrome/66.0.3359.139 Safari/537.36'})
        if module == 'pkurp':
            # url_podsistema=''
            # resp=self.br.get(url_podsistema)
            resp = self.br.get("http://{0}/users/auth/sia".format(self.pkurp_address))
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
        self.br.post(action, {'RelayState': RelayState, 'SAMLResponse': SAMLResponse})
        return
