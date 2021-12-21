import json
import os
import posixpath
from urllib.parse import urlparse

import requests
import unidecode
from goose3 import Goose
from tqdm import tqdm


def resolveComponents(url):
    """
     resolveComponents('http://www.example.com/foo/bar/../../baz/bux/')
    'http://www.example.com/baz/bux/'
     resolveComponents('http://www.example.com/some/path/../file.ext')
    'http://www.example.com/some/file.ext'
    """

    parsed = urlparse(url)
    new_path = posixpath.normpath(parsed.path)
    if parsed.path.endswith('/'):
        # Compensate for issue1707768
        new_path += '/'
    cleaned = parsed._replace(path=new_path)

    return cleaned.geturl()


def clean_article(item, article):
    def clean_text(text):
        text = text.strip()
        text = text.replace('“', '"').replace('”', '"')
        text = text.replace("‘", "'").replace("’", "'")
        return text

    abstract = item['abstract']
    caption = item['caption']
    article = clean_text(article)

    tips = 'As a subscriber, you have 10 gift articles to give each month. Anyone can read what you share.'
    article_cleaned = article.replace(abstract, '').replace(caption, '').replace(tips, '')
    while True:
        if article_cleaned.startswith('\n'):
            article_cleaned = article_cleaned[1:]
        else:
            break

    return article_cleaned


def download_image(item):
    img_data = requests.get(item['image_url'], stream=True).content
    with open(os.path.join("./images/%s.jpg" % (item['image_id'])), 'wb') as f:
        f.write(img_data)


def download_article(item):
    url = resolveComponents(item['article_url'])
    extract = g.extract(url=url)
    article = unidecode.unidecode(extract.cleaned_text)
    return article


def del_dir(path):
    for i in os.listdir(path):  # os.listdir(path_data)#返回一个列表，里面是当前目录下面的所有东西的相对路径
        file_data = path + '/' + i  # 当前文件夹的下面的所有东西的绝对路径
        if os.path.isfile(file_data):  # os.path.isfile判断是否为文件,如果是文件,就删除.如果是文件夹.递归给del_file.
            os.remove(file_data)


if __name__ == '__main__':
    g = Goose()
    if os.path.exists('./images'):
        del_dir('./images')
    else:
        os.makedirs('./images')
    j = json.load(open('nytimes_dataset.json', 'r', encoding='utf8'))
    new_j = []
    for item in tqdm(j):
        download_image(item)
        item['body'] = clean_article(item, download_article(item))
        new_j.append(item)
    json.dump(new_j, open('nytimes_dataset_full.json', 'w', encoding='utf8'))
