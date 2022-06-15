# Парсер автоматически (раз в шесть часов) собирает данные с сайта https://www.meteonova.ru/ о погодных условиях и
# состоянии почвы в разных городах(Ашхабад, Батуми, Владтвосток, Одесса, Москва, Рига), и упаковывает их в json.
# Первым шагом происходит запрос к сайту, затем что бы не спамить запросами вся страница выкачивается на машину и
# дальше уже парсится с использованием BeautifulSoup. При каждом запросе к сайту html страницы на машине
# перезаписываются, а по завершению парсинга обновлённые данные дополняют локальный сборник json-ов.


from time import sleep
import requests
from bs4 import BeautifulSoup
import datetime
import json


# Порядок обработки городов в словарях cities, urls, templates, jsons:
# Ашхабад, Батуми, Владтвосток, Одесса, Москва, Рига
cities = ['Ашхабад', 'Батуми', 'Владтвосток', 'Одесса', 'Москва', 'Рига']

urls = [
    'https://www.meteonova.ru/agro/38880.htm', 'https://www.meteonova.ru/agro/37484.htm',
    'https://www.meteonova.ru/agro/31960.htm', 'https://www.meteonova.ru/agro/33837.htm',
    'https://www.meteonova.ru/agro/27612.htm', 'https://www.meteonova.ru/agro/26422.htm'
]

templates = [
    './html/ashgabat.html', './html/batumi.html', './html/vladivostok.html',
    './html/odessa.html', './html/moscow.html', './html/riga.html'
]

jsons = ['./json/ashgabat.json', './json/batumi.json', './json/vladivostok.json',
         './json/odessa.json', './json/moscow.json', './json/riga.json'
]

# Заголовки для передачи в GET-запросах
headers = {
    'accept': '*/*',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
}


# Рабочий цикл, рассчитанный на автоматический сбор, обработку и сохранение данных раз в 6 часов.
while True:
    for i in range(6):
        print(f'Собираю данные о {cities[i]}')
        req = requests.get(urls[i], headers)

        soup = BeautifulSoup(req.content, 'lxml')
        with open(templates[i], 'w', encoding='utf-8') as msc:
            msc.write(soup.prettify())

        soup = BeautifulSoup(open(templates[i], encoding='utf-8'), 'html.parser')

        # Определение времени суток и состояния:
        date = datetime.date.today()
        soup_tod = soup.find(id='agro_content_weather0').find(class_='weather_td').find(class_='tod').text.strip()
        soup_phenom = soup.find(class_='weather_td').find(class_='phenom').find_next().get('alt')

        # Определение погоды на высоте 2м:
        soup_weather_block = soup.find(id='agro_content_weather2').find(class_='weather_td')
        soup_temper = soup_weather_block.find(class_='temper').text.strip()
        soup_moisture = soup_weather_block.find(class_='hum').text.strip()
        soup_wind = soup_weather_block.find(class_='wind').text.strip()
        soup_gow = soup_weather_block.find_all(class_='hum')[-1].text.strip()
        if len(soup_wind.strip().split()[0]) <= 3:
            soup_wind = f'{soup_wind.strip().split()[0]} {soup_wind.strip().split()[1]}'
        else:
            soup_wind = f'{soup_wind.strip().split()[0]}'

        # Определение состояние почвы:
        soup_soil = soup.find(id='agro_content_weather3').find(class_='weather_td')
        soup_soil_temper = soup_soil.find(class_='temper').string.strip()
        soup_soil_hum = soup_soil.find_all(class_='hum')
        soup_soil_precipitation = soup_soil_hum[0].text.strip()
        soup_soil_snow = soup_soil_hum[1].text.strip()
        soup_soil_snow_grow = soup_soil_hum[2].text.strip()
        soup_soil_snow_density = soup_soil_hum[3].text.strip()
        soup_soil_fire_class = soup_soil_hum[4].text.strip()

        # Определение состояние почвы (0-10см):
        soup_soil_top = soup.find(id='agro_content_weather4').find(class_='weather_td')
        soup_soil_top_temper = soup_soil_top.find(class_="temper").text.strip()
        soup_soil_top_moisture = soup_soil_top.find(class_="hum").text.strip()

        # Определение состояние почвы (10-40см):
        soup_soil_deep = soup.find(id='agro_content_weather5').find(class_='weather_td')
        soup_soil_deep_temper = soup_soil_deep.find(class_="temper").text.strip()
        soup_soil_deep_moisture = soup_soil_deep.find(class_="hum").text.strip()

        # Сборка
        data = {
            'Состояние:': {
                'Дата' : str(date),
                'Время суток': soup_tod,
                'Облачность': soup_phenom,
            },
            'Погода на высоте 2м:': {
                'Температура, с': soup_temper,
                'Влажность, %': soup_moisture,
                'Скорость ветра, м/с': soup_wind,
                'Порывы ветра, м/с': soup_gow,
            },
            'Состояние поверхности почвы:': {
                'Температура, с': soup_soil_temper,
                'Осадки, мм': soup_soil_precipitation,
                'Высота снега, м': soup_soil_snow,
                'Прирост снега за 3 ч.': soup_soil_snow_grow,
                'Плотность снега кг/м3': soup_soil_snow_density,
                'Класс пожаров (1-5)': soup_soil_fire_class,
            },
            'Cостояние почвы (0-10см):': {
                'Температура, с': soup_soil_top_temper,
                'Влажность, %': soup_soil_top_moisture,
            },
            'Cостояние почвы (10-40см):': {
                    'Температура, с': soup_soil_deep_temper,
                    'Влажность, %': soup_soil_deep_moisture,
            },
        }

        with open(jsons[i], 'r', encoding='utf-8') as file:
            data_list = json.load(file)
            data_list.append(data)
            with open(jsons[i], 'w+', encoding='utf-8') as file:
                json.dump(data_list, file, ensure_ascii=False, indent=4)
                print(f'Сбор данных о {cities[i]} завершен.')
    print('Все данные собраны. Ожидаю 6 часов.')
    sleep(21600)
