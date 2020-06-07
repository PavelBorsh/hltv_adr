import json
import time
import sys
from bs4 import BeautifulSoup
import requests


# Функция возвращает список ссылок на все матчи
def get_links(pages_num):
    if not (isinstance(pages_num, int)) or pages_num < 0:
        raise ValueError('page_num must be positive int')
    offset = 0
    can_get_next_page = True
    all_matches_output = []
    while can_get_next_page:
        r = requests.get(f'https://www.hltv.org/results?offset={offset}')

        parser = BeautifulSoup(r.text, 'html.parser')

        # Проверяем: а не кончились ли страницы
        find_end_of_results = parser.findAll('div')
        for i in find_end_of_results:
            if 'No results with the chosen filters' == i.text:
                print('Scan has ended.')
                can_get_next_page = False
                break

        # Парсим все матчи:
        all_matches = parser.findAll('div', class_='result-con')

        for match in all_matches:
            all_matches_output.append(match.find('a')['href'])

        offset += 100
        if offset > (pages_num - 1) * 100:
            break
    return all_matches_output


# Функция возвращает статистику конкретного матча
def get_match_stats(link):
    output_stats = {}
    r = requests.get('https://hltv.org' + link)
    parser = BeautifulSoup(r.text, 'html.parser')

    # Все названия карт, доступ через .text
    maps_tags = parser.findAll('div', class_=lambda x: x and x.endswith(' dynamic-map-name-full'))
    maps = [i.text for i in maps_tags]
    maps = maps[1:]
    table_totalstats = parser.findAll('table', class_='table totalstats')
    tr = [i.findAll('tr', class_='') for i in table_totalstats]
    output_stats['match'] = link
    output_stats['maps'] = {}
    for n_map, map_name in enumerate(maps, start=1):
        output_stats['maps'][map_name] = {}
        for j in tr[n_map * 2]:
            name = j.find('div', class_='smartphone-only statsPlayerName').text
            frags, deaths = j.find('td', class_='kd text-center').text.split('-')
            frags, deaths = int(frags), int(deaths)
            try:
                adr = float(j.find('td', class_='adr text-center').text)
            except AttributeError:
                adr = 0
            try:
                rating = float(j.find('td', class_='rating text-center').text)
            except AttributeError:
                rating = 0
            output_stats['maps'][map_name][name] = {
                'Frags': frags,
                'Deaths': deaths,
                'ADR': adr,
                'Rating 2.0': rating,
            }
        for j in tr[n_map * 2 + 1]:
            name = j.find('div', class_='smartphone-only statsPlayerName').text
            frags, deaths = j.find('td', class_='kd text-center').text.split('-')
            frags, deaths = int(frags), int(deaths)
            try:
                adr = float(j.find('td', class_='adr text-center').text)
            except AttributeError:
                adr = 0
            try:
                rating = float(j.find('td', class_='rating text-center').text)
            except AttributeError:
                rating = 0
            output_stats['maps'][map_name][name] = {
                'Frags': frags,
                'Deaths': deaths,
                'ADR': adr,
                'Rating 2.0': rating,
            }
    return output_stats


def save_to_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f)


def get_stats(pages_num):
    print('Collecting matches links...')
    start = time.monotonic()
    matches_links = get_links(pages_num)
    print('Collected.\n')
    print('Parsing stats...')
    all_data = {}
    counter = 0
    for n, link in enumerate(matches_links):
        percent_done = (n / len(matches_links) * 100)
        print('%.1f' % percent_done, '%', end='')
        all_data[n] = get_match_stats(link)
        time.sleep(0.1)  # Задержка менжу запросами, чтобы не банил сайт
        sys.stdout.write('\r')
        if len(all_data) - counter == 50:
            counter = len(all_data)
            save_to_json('hltv.json', all_data)
    t = round(time.monotonic() - start, 2)
    print(f'Data collected from {pages_num} pages in {t} seconds.')


def find_best_stats(filename, param='ADR'):
    max_param = 0
    match_link = ''
    with open(filename, 'r') as f:
        data = json.load(f)
    for match in data:
        for m in data[match]['maps']:
            for player in data[match]['maps'][m]:
                if data[match]['maps'][m][player][param] > max_param:
                    max_param = data[match]['maps'][m][player][param]
                    match_link = data[match]['match']
    return max_param, 'https://hltv.org' + match_link


if __name__ == '__main__':
    get_stats(226)
    # print(find_best_stats('hltv.json', 'Rating 2.0'))
