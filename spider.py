
from pyquery import PyQuery as py
import re
import pymongo
import time
import traceback
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *
from config import *

#代码用于使用selenium爬取"京东商城"里的美食信息并保存在mongodb库上
driver = webdriver.Chrome()
driver.maximize_window()
client = pymongo.MongoClient(mongo_url)
mydb = client[mongo_db]
#用selenium进入京东商场搜索美食，并返回搜索出来的页面
def search():
    print("正在搜索")
    driver.get("https://www.jd.com/")
    try:
        input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#key"))
        )
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#search > div > div.form > button"))
        )
        input.send_keys("美食")
        button.click()
        total = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#J_bottomPage > span.p-skip > em:nth-child(1) > b"))
        )
        data = get_product()
        save_to_mongo(data)
        return total.text

    except TimeoutException:
        print("搜索失败")
        return search()

#收集页面需要的商品信息到mongodb并点击下一页
def next_page(page):
    print("正在翻页")
    try:
        print(page)
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
        time.sleep(1)
        print("等待结束")
        input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#J_bottomPage > span.p-skip > input"))
        )
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#J_bottomPage > span.p-skip > a"))
        )
        input.clear()
        input.send_keys(page)
        button.click()
        element = WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#J_bottomPage > span.p-num > a.curr"), str(page))
        )
        data = get_product()
        save_to_mongo(data)

    except TimeoutException:
        print("翻页失败")
        return next_page(total)
#解析页面内容的方法
def get_product():
    print("正在获取产品信息")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#J_goodsList > ul .gl-item"))
    )
    html = driver.page_source
    """通过用bs4的方式解析文档
    soup = bs(html)
    items2 = soup.find(id='J_goodsList').find_all(class_='gl-item')
    for i in items2:
        d1 = i.find(class_='p-img')
        #print("d1:",d1)
        d2 = d1.find('img')
        print("d2:",d2)
        date2 = {"img" : d2.attrs['src']}
        print(date2)"""
    doc = py(html)
    items = doc('#J_goodsList > ul .gl-item').items()
    for item in items:
        img = item.find(' div > div.p-img > a > img').attr('src')
        if img:
            img = img
        else:
            img = item.find(' div > div.p-img > a > img').attr('data-lazy-img')
        data = {
            "img": img,
            "price": item.find('.p-price').text() ,
            "title":item.find('.p-name.p-name-type-2 em').text().replace('\n',""),
            "commit":item.find('.p-commit').text(),
            "shop":item.find('.p-shop').text()
        }
        return data



#保存到mongodb上
def save_to_mongo(data):
    if mydb[mongo_table].insert_one(data):
        print("插入成功")
        return True
    else:
        print("插入失败")
        return False


def main():
    total = int(search())
    for i in range(2,total+1):
        next_page(i)


if __name__ == '__main__':
    main()
