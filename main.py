import time

import pkurp.browser as pkurp_browser
import ppoz.browser as ppoz_browser
import pdf.pdfminerdef as pdfminer_def
import concurrent.futures
import json

from bs4 import BeautifulSoup

def encumbrance_edit_in_pkurp(pvd_number):
    '''
    Редактирует сведения по ограничению в ПКУРП, получаемое значение № обращения
    '''
    pk_browser = auth_br
    pk_browser.pvd_number = pvd_number
    print('0) запускаем проверки на возможность обработки обращения')
    if not pk_browser.pvd_number:
        print('Функции не передан номер обращения')
        return

    if 'Other' not in pk_browser.pvd_number:
        print('%s - обращение не Other' % pk_browser.pvd_number)
        return pk_browser.pvd_number

    # pk_browser.get_registry_records(pvd_number)
    pk_browser.get_registry_data_container_records(pvd_number)

    # Проверка заявления что в работе у регистратора под которым происходит вход в ПКУРП
    if not pk_browser.curent_zayv_status_in_work:
        print('%s - в работе у другого пользователя' % pvd_number)
        return pvd_number

    pk_browser.get_registry_records_list()
    if len(pk_browser.registry_records_list) == 0:
        print('%s - пустой список Сведений ЕГРН' % pvd_number)
        return pvd_number

    # # 'http://pkurp-app-balancer-01.prod.egrn/api/requests/Other-2021-12-07-021834/find_type_records?region=12&section_number=12:05:3301001:6566&type=restrict_record&active_only=false&limit=10&skip=0'
    # restrict_record_list = pk_browser.get_restrict_record_list('12:05:3301001:6566')
    # print(restrict_record_list)

    # Получаем все заявления с документами
    pk_browser.get_all_from_statements()

    # обновить сведения егрн
    # pk_browser.refresh_registry_records()

    success = False
    for statement in pk_browser.statements:
        # print(statement)
        print('1) собираем заявления из обращения')
        print(statement['name'])
        print('######################################')
        for doc in statement['docs']:
            print(doc['name'])
            print('В докменте присутствуют следующие типы ссылок: ', doc['type'])
            print('________________________________________________________')
            if 'XML' in doc['type']:
                try:
                    # if pk_browser.get_name_document(doc['soup'].find(
                    #         'doccode').text) == 'Постановление о снятии запрета на совершение действий по регистрации':
                    #     print('Нашел.')
                    action_code = doc['content'].find(['actioncode', 'stcom:actioncode', 'ns2:actioncode'])
                    # action_code = None
                    # if doc['content'].find('actioncode') is None:
                    #     if doc['content'].find('stcom:actioncode') is not None:
                    #         action_code = doc['content'].find('stcom:actioncode').text
                    # else:
                    #     action_code = doc['content'].find('actioncode').text
                    if action_code is None:
                        print('В XML файле не найден тег actioncode')
                        print('<Start--------------->')
                        print(doc['content'])
                        print('<-End--------------->')
                        continue
                    # XML - заявление
                    # 659311111116 - Прекращение ограничений прав на объект недвижимости и обременений объекта недвижимости
                    if action_code.text == '659311111116':
                        print('---->Заявление №' + statement[
                            'document_number'] + ' на прекращение ограничений прав на объект недвижимости и обременений объекта недвижимости')

                        # Является обязательным, без кадастрового номера не ищет ограничения
                        doc_cadastralnumber = doc['content'].find(['ns5:cadastralnumber', 'obj:cadastralnumber', 'ns7:cadastralnumber'])
                        if not (doc_cadastralnumber is None):
                            doc_cadastralnumber = doc_cadastralnumber.text.strip()

                        # Номер ограничения, которую гасят
                        doc_mortgageregnumber = doc['content'].find(['ns4:mortgageregnumber', 'mortgageregnumber', 'ns6:mortgageregnumber'])
                        if not (doc_mortgageregnumber is None):
                            doc_mortgageregnumber = doc_mortgageregnumber.text.strip()
                        # print(doc_mortgageregnumber)

                        doc_mortgageregdate = doc['content'].find(['ns4:mortgageregdate', 'mortgageregdate', 'ns6:mortgageregdate'])
                        if not (doc_mortgageregdate is None):
                            doc_mortgageregdate = doc_mortgageregdate.text.strip()

                        doc_subject = doc['content'].find(['ns7:name', 'subj:name', 'ns5:name'])
                        if not (doc_subject is None):
                            doc_subject = doc_subject.text.strip()

                        # document_date = datetime.datetime.strptime(datetime.datetime.fromisoformat(doc['content'].find('creationdate').text.strip()), "%d-%m-%Y")
                        # document_date = datetime.datetime.fromisoformat(doc['content'].find('creationdate').text.strip())

                        document_date = doc['content'].find(['creationdate', 'stcom:creationdate', 'ns2:creationdate'])
                        if not (document_date is None):
                            document_date = document_date.text.encode('iso-8859-1').decode()

                        # print('ns5:cadastralnumber:', doc['content'].find('ns5:cadastralnumber').text.strip())

                        # Список Ограничения/обременения
                        restrict_record_list = pk_browser.get_restrict_record_list(doc_cadastralnumber)
                        # print(restrict_record_list)

                        for rec_restrict in restrict_record_list:
                            # print(rec_restrict)
                            # and rec_restrict['registration_date'] == doc_mortgageregdate
                            # print(rec_restrict['business_number'], ' == ', doc_mortgageregnumber)
                            if rec_restrict['business_number'] == doc_mortgageregnumber:
                                print('Можно погасить Ограничения/обременения')
                                # print(rec_restrict)

                                # закомментировано для проверки
                                # запускаем погашение обременения по регистрационному номеру
                                print('2) запускаем погашение обременения по регистрационному номеру')
                                resp = pk_browser.extinguish_encumbrance(rec_restrict['record_number'])
                                # print(resp.text)
                                s = BeautifulSoup(resp.text, 'lxml')

                                # self.curent_token_record=s.find('input',{'name':'authenticity_token'})['value']
                                edit_path = s.find('form', {'id': 'edit_registry_data_container'})['action']
                                underlying_documents_id = json.loads(
                                    s.find('div', {'data-class-name': 'RegistryData::UnderlyingDocumentsHolder'})[
                                        'data-data'].replace('&quot;', '"'))['_id']['$oid']
                                current_token_record_edit = s.find('meta', {'name': 'csrf-token'})['content']
                                current_edit_record = json.loads(
                                    s.find('div', {'class': 'react-form'})['data-data'].replace('&quot;', '"'))

                                # добавление (изменение) документов основания в формируемых сведений
                                docs = []
                                add_doc_ref = {
                                    'doc_code': 'Заявление о погашении регистрационной записи об ипотеке (статья 53 Закона, статья 25 Федерального закона от 16 июля 1998 г. N 102-ФЗ "Об ипотеке (залоге недвижимости)"',
                                    'doc_name': u"Заявление {0} о погашение регистрационной записи об ипотеке".format(
                                        doc_subject),
                                    'doc_number': statement['document_number'],
                                    'doc_date': document_date
                                }
                                docs.append(add_doc_ref)
                                for doc_ref in doc['content'].findAll(['applieddocument', 'stcom:applieddocument', 'ns2:applieddocument']):
                                    # добавляем все документы из заявления кроме:
                                    # 558301010000 - Доверенность
                                    # 008001001000 - Паспорт гражданина Российской Федерации
                                    # 008002099000 - Иной документ
                                    doc_type_code = doc_ref.find(['ns2:documenttypecode', 'doc:documenttypecode', 'ns3:documenttypecode'])
                                    if not (doc_type_code is None) and doc_type_code.text.strip() != '558301010000' and doc_type_code.text.strip() != '008001001000':
                                        doc_name = doc_ref.find(['ns2:name', 'doc:name', 'ns3:name'])
                                        if not (doc_name is None):
                                            doc_name = doc_name.text.strip()

                                        doc_number = doc_ref.find(['ns2:number', 'doc:number', 'ns3:number'])
                                        if not (doc_number is None):
                                            doc_number = doc_number.text.strip()

                                        doc_date = doc_ref.find(['ns2:issuedate', 'doc:issuedate', 'ns3:issuedate'])
                                        if not (doc_date is None):
                                            doc_date = doc_date.text.strip()

                                        add_doc_ref_new = {
                                            'doc_code': doc_name,
                                            'doc_name': doc_name,
                                            'doc_number': doc_number,
                                            'doc_date': doc_date
                                        }

                                        if doc_type_code.text.strip() != '008002099000' and doc_type_code.text.strip() != '558402990000' and doc_type_code.text.strip() != '558403990000':
                                            docs.append(add_doc_ref_new)
                                        else:
                                            # ищем pdf иного документа и его ссылку
                                            for next_doc in statement['docs']:
                                                if 'PDF' in next_doc['type'] and next_doc['name'] == 'Иной документ':
                                                    pdf_content = pdfminer_def.pdf_from_url_to_txt(next_doc['pdf_link'])
                                                    # print(pdfminer_def.get_doc_details(pdf_content))
                                                    pdf_doc_details = pdfminer_def.get_doc_details(pdf_content)
                                                    if 'error' not in pdf_doc_details and pdf_doc_details['number'] == doc_ref.find(['ns2:number', 'doc:number', 'ns3:number']).text.strip():
                                                        # подставляем реквизиты из pdf
                                                        add_doc_ref_new = {
                                                            'doc_code': pdf_doc_details['name'],
                                                            'doc_name': pdf_doc_details['name'],
                                                            'doc_number': pdf_doc_details['number'],
                                                            'doc_date': pdf_doc_details['date']
                                                        }
                                            docs.append(add_doc_ref_new)

                                print('3) добавление документов основания формируемых сведений')
                                print(json.dumps(docs, indent=4, sort_keys=True))
                                resp = pk_browser.change_reference_document(docs, current_edit_record,
                                                                            current_token_record_edit,
                                                                            underlying_documents_id, edit_path,
                                                                            doc_subject)
                                # print(resp.status_code)
                                if resp.status_code == 200:
                                    success = True

                        # print('Source text decode:', doc['soup'])

                    # # Encoding in UTF-8
                    # print('<===================================>')
                    # encoded_bytes = doc['soup'].encode('utf-8', 'replace')
                    # # Trying to decode via ASCII, which is incorrect
                    # # decoded_incorrect = encoded_bytes.decode('ascii', 'replace')
                    # decoded_correct = encoded_bytes.decode('utf-8', 'replace')
                    # # print('Incorrectly Decoded string:', decoded_incorrect)
                    # print('Correctly Decoded string:', decoded_correct)
                    # print('<!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!>')

                except Exception as e:
                    print("Ошибка обработки XML:", doc['name'])
                    print(str(e))
                    # print('<Start--------------->')
                    # print(doc['content'])
                    # print('<-End--------------->')
            print('')

    if success:
        print('4) запускаем проверки на закладке Список проверок')
        pk_browser.spisok_proverok_reload()
        time.sleep(5)
        print('5) проверяем Список проверок')
        if pk_browser.spisok_proverok_result(pvd_number, 0):
            print('5_1) проверки пройдены переводим движки 4 пункт: Проверка вида объекта недвижимого имущества')
            pk_browser.manual_proverki_submit()
            print('6) передаем на следующую стадию (Подписание)')
            result = pk_browser.compleate_encumbrance(pvd_number)
            print(f'Завершена обработки обращения {pvd_number} имеет статус {result}')
        else:
            print('5_1) проверки не пройдены или зависли.')


def arest_edit_in_pkurp(pvd_number):
    '''
    Редактирует сведения по арестам в ПКУРП, получаемое значение № обращения
    '''
    # print(pvd_number,user_name,password)
    # pk_browser=pkurp_browser.PKURP_Browser('prom')
    # pk_browser.init_podsistema('pkurp',user_name,password)
    pk_browser = auth_br
    # params={'filter':'mine','order[by]':'execution_date','number':pvd_number,'commit':'Применить'}
    # print('test')
    # pvd_number=pk_browser.find_requests(**params)['pkpvd_number']
    pk_browser.pvd_number = pvd_number
    # print('test1')
    # time.sleep(3)
    if not pk_browser.pvd_number:
        return
    if 'Other' not in pk_browser.pvd_number:
        return pk_browser.pvd_number
    # pk_browser.get_registry_records(pvd_number)
    pk_browser.get_registry_data_container_records(pvd_number)

    if not pk_browser.curent_zayv_status_in_work:
        return pvd_number

    pk_browser.get_registry_records_list()
    if len(pk_browser.registry_records_list) == 0:
        return pvd_number

    pk_browser.get_xml_from_doc()
    if pk_browser.get_name_document(pk_browser.xml_soup.find(
            'doccode').text) == 'Постановление о снятии запрета на совершение действий по регистрации':
        pk_browser.sniatie_arest()
        pk_browser.spisok_proverok_reload()
        pk_browser.manual_proverki_submit()
        pk_browser.compleate_arest(pvd_number)
    # pk_browser.br.close
    # print('test')

    elif pk_browser.get_name_document(pk_browser.xml_soup.find(
            'doccode').text) == 'Постановление о запрете на совершение действий по регистрации':
        pk_browser.get_registry_data_container_records(pvd_number)
        for key in pk_browser.registry_records.keys():
            # print('Zapret',pvd_number,key)
            pk_browser.edit_tabs_react_restrictions_encumbrances_data(key, pk_browser.registry_records[key][2])
        pk_browser.spisok_proverok_reload()
        pk_browser.manual_proverki_submit()
        pk_browser.compleate_arest(pvd_number)
    # pk_browser.br.close
    return pvd_number


def run_parallel(run_function, list_arguments, m_workers):
    '''
    Запускает параллельное выполнение: название функции, список передаваемых значений, число одновременно выполняемых потоков
    '''
    global auth_br
    pk_browser = pkurp_browser.PKURP_Browser('prom')
    pk_browser.init_module('pkurp', user_name, password)
    pk_browser.region = objectRegions
    auth_br = pk_browser
    count = 0
    with concurrent.futures.ProcessPoolExecutor(max_workers=m_workers) as executor:
        for num in zip(list_arguments, executor.map(run_function, list_arguments)):
            count += 1
            print(num, '-', '%s/%s' % (count, len(list_arguments)))


def test_get_doc_details(appeal_numbers):
    global auth_br
    pk_browser = pkurp_browser.PKURP_Browser('prom')
    pk_browser.init_module('pkurp', user_name, password)
    pk_browser.region = objectRegions
    auth_br = pk_browser
    pk_browser.pvd_number = appeal_numbers

    # Получаем все заявления с документами
    pk_browser.get_all_from_statements()
    for statement in pk_browser.statements:
        for doc in statement['docs']:
            print(doc['name'])
            print('В докменте присутствуют следующие типы ссылок: ', doc['type'])
            print('________________________________________________________')
            if 'PDF' in doc['type']:
                # print(doc['content'])
                print(doc['pdf_link'])
                pdf_content = pdfminer_def.pdf_from_url_to_txt(doc['pdf_link'])
                print(pdf_content)
                print(pdfminer_def.get_doc_details(pdf_content))
                # print(pdf_content)


def test_spisok_proverok_result(appeal_numbers):
    global auth_br
    pk_browser = pkurp_browser.PKURP_Browser('prom')
    pk_browser.init_module('pkurp', user_name, password)
    pk_browser.region = objectRegions
    auth_br = pk_browser
    pk_browser.pvd_number = appeal_numbers
    print(pk_browser.spisok_proverok_result(appeal_numbers, 0))


def test_encumbrance_edit_in_pkurp(appeal_numbers):
    global auth_br
    pk_browser = pkurp_browser.PKURP_Browser('prom')
    pk_browser.init_module('pkurp', user_name, password)
    pk_browser.region = objectRegions
    auth_br = pk_browser
    pk_browser.pvd_number = appeal_numbers
    encumbrance_edit_in_pkurp(appeal_numbers)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # print_hi('PyCharm')
    global user_name
    global password
    global objectRegions
    objectRegions = 12
    user_name = ''
    password = ''
    number_of_threads = 10
    ppoz_browser = ppoz_browser.PPOZ_Browser('prom')
    # print(user_name)
    ppoz_browser.init_module('ppoz', user_name, password)
    # list_numbers = ppoz_browser.get_pristav_in_work(objectRegions, subjectRF, executorDepartments, user_name)

    # post_data = {"pageNumber": 0, "pageSize": 10, "RequestTypes": ["111300021000"], "objectRegions": [12],
    #              "subjectRF": [12], "executorDepartments": [12.028], "executors": ["smkudriavtcev"],
    #              "byActiveExecutor": True, "statuses": ["sentToProcessing"]}

    post_data = {
        "pageNumber": 0,
        "pageSize": 10,
        "actionCodes": [
            "659311111116"
        ],
        "statuses": [
            "pkurp_validations"
        ],
        "subjectRF": [
            "12"
        ],
        "executorDepartments": [
            "12.028"
        ],
        "executors": [
            "smkudriavtcev"
        ],
        "byActiveExecutor": 'true',
        "senderTypes": [
            "Other"
        ],
        # "appealNumber": "Other-2021-12-27-142068"
    }
    url = "http://ppoz-service-bal-01.prod.egrn:9001/manager/requests"
    list_numbers = ppoz_browser.get_appeal_numbers(url, post_data)

    # print(list_numbers);

    # list_numbers = ['PKPVDMFC-2021-11-03-000142']
    # list_numbers = ['Other-2021-12-10-656411']
    # list_numbers = ['Other-2021-12-11-357322']
    # list_numbers = ['Other-2021-12-07-021834']
    # list_numbers = ['Other-2021-12-21-347248']
    # list_numbers = ['PKPVDMFC-2021-12-25-139460']

    # Запускаем параллельное выполнение: название функции, список передаваемых значений, число одновременно выполняемых потоков
    # run_parallel(arest_edit_in_pkurp, list_numbers, number_of_threads)
    run_parallel(encumbrance_edit_in_pkurp, list_numbers, number_of_threads)

    # test_get_doc_details('Other-2021-12-21-347248')
    # test_get_doc_details('Other-2022-01-17-563140')

    # arest_edit_in_pkurp(list_numbers[0])

    # тест погашение ограничения
    # test_encumbrance_edit_in_pkurp('Other-2022-01-13-485129')

    # pk_browser.pvd_number = list_numbers[0]
    # pk_browser.manual_proverki_submit()

    # # для проверки запущеного списка проверок spisok_proverok_result()
    # test_spisok_proverok_result('Other-2021-12-25-038963')
