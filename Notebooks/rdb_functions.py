from bs4 import BeautifulSoup
import numpy
import requests
from scrapy import Selector
import pandas as pd
import unidecode
from itertools import compress
from sklearn.linear_model import LinearRegression
import unidecode
import time

#### FUNCTIONS TO GIVE STRUCTURE TO THE SCRAPPED DATA ###########################

def clean_m2(list1):
    '''
    This functions clean the list of square meters
    '''
    return [int(i.split()[0].replace(',','')) for i in list1]


def clean_price(list1):
    '''
    This functions clean the list of prices
    '''
    return [int(i.split()[0].replace(',','')) for i in list1]

def clean_adress(list1):
    '''
    This functions clean the list of adress
    '''
    return [unidecode.unidecode(i.replace(',','+').lower()) for i in list1]
    
    

def paste_url(mun,est):
    '''
    This function takes municipalities and states, paste them and return metroscubicos url to scrap
    '''
    mun=unidecode.unidecode(mun.replace(' ','-').lower())
    est=unidecode.unidecode(est.replace(' ','-').lower())
    url='https://inmuebles.metroscubicos.com/casas/venta/'+mun+'/'+est+'/#origin=search&as_word=true'
    return url

def clean_list(list_):
    '''
    This function clean the list from html format
    '''
    result=[]
    for item in list_:  
        v1=item.find('>')
        v2=item.find('<',2)
        result.append(item[v1+1:v2])
    return result

def clean_list_url(list_):
    '''
    This function clean the list to to get the https
    '''
    result=[]
    for item in list_:  
        v1=item.find('href=')
        v2=item.find('>')
        item=item[v1+5:v2]
        item=item.replace("\"","")
        result.append(item)
    return result

def scrapping_atr(url):
    
    '''
    This function scrap the websites
    '''
    try:
        html = requests.get( url ).content
        sel = Selector( text = html )
    except:
        print(f'This url didnt work: \n {url}')

    try:
        path='//*[@class="ui-search-card-attributes ui-search-item__group__element"]'
        aux=sel.xpath(path).extract()
        cl=['m²'in i for i in aux]
        path='//*[@class="ui-search-card-attributes__attribute"]'
        aux=sel.xpath(path).extract()
        aux=clean_list(aux)
        cl_m=['m' in i for i in aux]
        m2=clean_m2(list(compress(aux, cl_m)))
    except:
        print(f'no square meters info in:\n{url}')

    try:
        path='//*[@class="price-tag-text-sr-only"]'
        aux=sel.xpath(path).extract()
        price=clean_price(clean_list(aux))
        price=list(compress(price,cl))
    except:
        print(f'no prices info in:\n{url}')

    try:
        path='//*[@class="ui-search-result__image"]/a/@href'
        aux=sel.xpath(path).extract()
        urls=clean_list(aux)
        urls=list(compress(urls,cl))
    except:
        print(f'no urls info in:\n{url}')

    try:
        path='//*[@class="ui-search-item__group__element ui-search-item__location"]'
        aux=sel.xpath(path).extract()
        adress=clean_adress(clean_list(aux))
        adress=list(compress(adress,cl))
    except:
        print(f'no adress info in:\n{url}')

    try:
        path='//*[@class="andes-pagination__button andes-pagination__button--next"]/a/@href'
        next_url=sel.xpath(path).extract()[0]
    except:
        next_url=''
        print(f'no further link info in:\n{url}')
        print('_'*30)

    try:
        p_m=[a/b for a,b in zip(price,m2)]
        result=pd.DataFrame({'p_m':p_m,'m2':m2,'price':price,'adress':adress,'url':urls})
        return [next_url,result]
    except:
        print('Error: some data were missed.')

        
############### FUNCTIONS FOR THE MODEL ##################################

def generate_b1_b0(dataframe,column_x,column_y):
    '''
    This function generates the constant and coefficient from a linear regression of two columns x and y.
    '''
    try:
        y=dataframe[column_y][~dataframe[column_y].isna()]
        x=dataframe[column_x][~dataframe[column_y].isna()]
        x=numpy.array(x).reshape((-1, 1))
        y=numpy.array(y)
        model = LinearRegression()
    
        model.fit(x, y)
        model = LinearRegression().fit(x, y)
        return [model.coef_[0],model.intercept_]
    except:
        print(f'There were problems with {column_x} and {column_y}')
        return[numpy.nan,numpy.nan]

def fill_nas(vector_y,vector_x,b1_b0):
    '''
    This function replace NAs with a predicted value greater or equal than zero
    '''
    try:
        result=vector_y.copy()
        cl=vector_y.isna()
        result[cl]=b1_b0[0]*vector_x+b1_b0[1]
        result[result<0]=0
        
        return result
    except:
        print(f'It didnt work for {vector_y} and {vector_x}, b1= {b1_b0[0]}')