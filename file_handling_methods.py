import os
import pandas as pd
import requests
import my_logger
from flask import abort
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from postgres import sqlalch_db_conn_str, connection_args, psql_insert_copy, DB, db_connection_string

logger = my_logger.init_logger("file_handling_methods")


def upload_prices(file_path, api_id, **kwargs):
    if os.path.splitext(file_path)[1] == '.csv':
        df = pd.read_csv(file_path)
    else:  # .xlsx or .xls
        df = pd.read_excel(file_path)
    print(df)
    expected_headers = ['offer_id', 'price']
    if not (list(df.columns) == expected_headers):
        logger.warning("400 Bad file structure")
        abort(400, description="Bad file structure.")
    offer_ids = df['offer_id'].tolist()
    try:
        prices = df['price'].astype(float).tolist()
    except ValueError:
        logger.warning("400 Bad file structure")
        abort(400, description="Bad file structure.")

    data = {"api_id": api_id,
            "offer_id": offer_ids,
            "price": prices}
    url = "https://apps0.ecomru.ru:4446/prices"
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.warning(repr(e))
        abort(502, description=repr(e))
    filename = os.path.basename(file_path)
    return {"message": f"Client file: {filename} is successfully saved and prices are uploaded."}


def upload_min_margin(file_path, api_id, **kwargs):
    if os.path.splitext(file_path)[1] == '.csv':
        df = pd.read_csv(file_path)
    else:  # .xlsx or .xls
        df = pd.read_excel(file_path)
    print(df)
    expected_headers = ['offer_id', 'margin']
    if not (list(df.columns) == expected_headers):
        logger.warning("400 Bad file structure")
        abort(400, description="Bad file structure.")
    offer_ids = df['offer_id'].tolist()
    try:
        margin = df['margin'].astype(float).tolist()
    except ValueError:
        logger.warning("400 Bad file structure")
        abort(400, description="Bad file structure.")

    data = {"api_id": api_id,
            "offer_id": offer_ids,
            "min_margin": margin}
    url = "https://apps0.ecomru.ru:4446/margins"
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.warning(repr(e))
        abort(502, description=repr(e))
    filename = os.path.basename(file_path)
    return {"message": f"Client file: {filename} is successfully saved and min margin are uploaded."}


def upload_ya_impressions_and_sales(file_path, api_id, **kwargs):
    if os.path.splitext(file_path)[1] == '.csv':
        df = pd.read_csv(file_path)
    else:  # .xlsx or .xls
        df = pd.read_excel(file_path)
    expected_headers = ['Название бизнес аккаунта', 'Тип бизнес аккаунта', 'ID бизнес аккаунта',
                        'Магазин', 'ID магазина', 'День', 'Месяц', 'Год', 'ID округа',
                        'Федеральный округ', 'ID бренда', 'Бренд', 'ID категории', 'Категория',
                        'Ваш SKU', 'Название товара', 'Показы', 'Добавлено в корзину, шт.',
                        'Конверсия добавления в корзину, %', 'Продажи, шт.',
                        'Цена товара, руб.', 'Продажи, руб.']
    if not (list(df.columns) == expected_headers):
        logger.warning("400 Bad file structure")
        abort(400, description="Bad file structure.")

    new_headers = {'Ваш SKU': 'sku_id', 'Название товара': 'sku_name', 'День': 'date',
                   'ID категории': 'category_id', 'Категория': 'category_name',
                   'ID бренда': 'brand_id', 'Бренд': 'brand_name',
                   'Показы': 'session_view', 'Добавлено в корзину, шт.': 'hits_tocart',
                   'Конверсия добавления в корзину, %': 'conv_tocart', 'Продажи, шт.': 'delivered_units',
                   'Продажи, руб.': 'revenue', 'ID округа': 'region_id', 'Федеральный округ': 'region_name'}
    headers_list = list(new_headers.keys())
    df = df[headers_list]
    df.rename(columns=new_headers, inplace=True)
    df['api_id'] = api_id
    try:
        engine = create_engine(sqlalch_db_conn_str, connect_args=connection_args)
        df.to_sql('data_analytics_bydays_main', engine, if_exists='append', method=psql_insert_copy, index=False)
        logger.info(f"Yandex impressions and sales data for api_id {api_id} saved in db.")
    except (Exception, SQLAlchemyError) as e:
        logger.error(repr(e))
    with DB(db_connection_string) as db:
        db.delete_duplicates_from_data_analytics_bydays_main_table()


def upload_yandex_sales_boost(file_path, api_id, **kwargs):
    if os.path.splitext(file_path)[1] == '.csv':
        df = pd.read_csv(file_path)
    else:  # .xlsx or .xls
        df = pd.read_excel(file_path)
    expected_headers = ['Название бизнес аккаунта', 'Тип бизнес аккаунта', 'ID бизнес аккаунта',
                        'Магазин', 'ID магазина', 'Начало периода', 'Конец периода', 'Ваш SKU',
                        'Наименование предложения', 'Продано с помощью продвижения, шт',
                        'Продано с помощью продвижения, рубли', 'Расход на продвижение, рубли',
                        'Расход на продвижение, %', 'Средняя стоимость продвижения',
                        'Продано всего, шт', 'Продано всего, рубли', 'Количество, шт',
                        'Доля продаж у партнера', 'Клики по товарам со ставками, шт.',
                        'Все клики, шт.', 'Заказано товаров со ставками, шт.',
                        'Всего заказано товаров, шт.']
    if not (list(df.columns) == expected_headers):
        logger.warning("400 Bad file structure")
        abort(400, description="Bad file structure.")
    print(df.head())
    # Delete last row
    df = df.iloc[:-1]
    new_headers = {'Ваш SKU': 'sku_id', 'Наименование предложения': 'sku_name', 'День': 'date',
                   'Клики по товарам со ставками, шт.': 'hits_view_search', 'Все клики, шт.': 'hits_view',
                   'Продано всего, шт': 'delivered_units', 'Продано всего, рубли': 'revenue',
                   'Всего заказано товаров, шт.': 'ordered_units', 'Расход на продвижение, рубли': 'adv_sum_all',
                   'Заказано товаров со ставками, шт.': '', 'Продано с помощью продвижения, рубли': '',
                   'Продано с помощью продвижения, шт': '',
                   'ID округа': 'region_id', 'Федеральный округ': 'region_name'}
    headers_list = list(new_headers.keys())
    df = df[headers_list]
    df.rename(columns=new_headers, inplace=True)
    df['api_id'] = api_id


def upload_offers_mapping_table(file_path, client_id, **kwargs):
    if os.path.splitext(file_path)[1] == '.csv':
        df = pd.read_csv(file_path)
    else:  # .xlsx or .xls
        df = pd.read_excel(file_path)
    if df.isnull().values.any():
        logger.warning("400 Bad file structure")
        abort(400, description="Bad file structure.")
    mappings = df.to_dict('list')
    data = {'client_id': client_id,
            'mappings': mappings}
    url = "https://apps0.ecomru.ru:4446/mappings"
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.warning(repr(e))
        abort(502, description=repr(e))
    filename = os.path.basename(file_path)
    return {"message": f"Client file: {filename} is successfully saved and offers mapping table are uploaded."}


if __name__ == "__main__":
    pass
    # upload_ya_impressions_and_sales("impressions.xlsx", 1)
    # upload_yandex_sales_boost("boost.xlsx")
    # print(upload_prices('price.xlsx', 1))
    # print(upload_min_margin('margin.xlsx', 1))
    # print(upload_offers_mapping_table('price.xlsx', 1))
