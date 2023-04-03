import scrapy
import re
from scrapy.http import Request
from scrap.myclass import version, mod
import time


class CurseforgeSpider(scrapy.Spider):
    name = "curseforge"
    allowed_domains = ["mcmod.cn"]
    basic_domain = "https://www.mcmod.cn/"
    # start_urls = ["https://www.mcmod.cn/class/513.html",]
    # start_urls = ["https://www.mcmod.cn/class/918.html",]
    # start_urls = ["https://www.mcmod.cn/class/5343.html",]
    start_urls = ["https://www.mcmod.cn/class/2021.html", ]
    all_results = []

    def parse(self, response):
        def get_subcollection(tag, index):
            base_pat = "li["+str(index)+"]"
            legend = tag.xpath(base_pat+'/span/text()').extract()
            content = tag.xpath(base_pat+'/ul/li/a/text()').extract()
            href = tag.xpath(base_pat+'/ul/li/a/@href').extract()
            return (legend, content,href)

        def get_table(tag, index):
            ver = tag.xpath("./fieldset["+str(index)+"]/legend/text()").extract()
            sub_tag = tag.xpath("./fieldset["+str(index)+"]")
            return (ver, sub_tag)

        def get_ver(tag, index):
            platform_tag = tag.xpath("./ul["+str(index)+"]")
            platform = platform_tag.xpath("./li/text()").extract()
            ver = platform_tag.xpath("li/a/text()").extract()
            return (platform, ver)

        def f_keyword(keyword, dict):
            r = re.compile(keyword)
            keys = list(filter(r.match, dict.keys()))
            return [dict[keys[i]] for i in range(len(keys))]

        def get_ver_dict():
            vertag = response.xpath("/html/body/div[2]/div/div[2]/div[2]/div[1]/div[2]/div[2]/div[1]/ul/li/ul")
            i = 1
            ver_dict = {}
            while True:
                platform, ver = get_ver(vertag, i)
                if platform and ver:
                    i += 1
                    ver_dict[platform[0]] = ver
                else:
                    break
            return ver_dict

        def get_mod_dict():
            mod_relation_tag = response.xpath("/html/body/div[2]/div/div[2]/div[2]/div[1]/div[5]/ul/li[2]/ul")
            i = 1
            outer_dict = {}
            while True:
                table_ver, table = get_table(mod_relation_tag, i)
                j = 1
                inner_dict = {}
                while True:
                    legend, content, href = get_subcollection(table, j)
                    if legend and content:
                        j+=1
                        inner_dict[legend[0]] = [content,href]
                    else:
                        break
                if table_ver and table:
                    i+=1
                else:
                    break
                outer_dict[table_ver[0]] = inner_dict
            return outer_dict

        def get_mod_by_kwd(keyword, mod_dict):
            tmp_dict = {}
            for ver, mods in mod_dict.items():
                tmp_list = f_keyword(keyword, mods)
                if tmp_list:
                    if len(tmp_list) > 1:
                        print(tmp_list)
                        print(mod_dict)
                        exit(1)
                    else:
                        tmp_dict[ver] = tmp_list[0]
            return tmp_dict

        def get_mod_by_platform(platform, mod_dict):
            new_dict = {}
            r = re.compile(platform)
            keys = list(filter(r.match, list(mod_dict.keys())))
            for k in keys:
                new_dict[k] = mod_dict[k]
            return new_dict

        ver_dict = get_ver_dict()
        mod_dict = get_mod_dict()
        yield mod_dict
        yield Request(url="https://www.mcmod.cn/class/5343.html", callback=self.parse)


    def start_requests(self):
        yield Request(url="https://www.mcmod.cn/class/5343.html", callback=self.parse_recursive)

    def parse_recursive(self, response):
        # ... your parsing code ...
        # from importlib import reload
        # import scrap.myclass
        # reload(scrap.myclass)
        # from scrap.myclass import version, mod
        current_mod = mod.init_from_href(response.url)
        current_mod.extract_info(response)
        self.all_results += list(current_mod.relation_raw.keys())
        for _ in list(list(current_mod.relation_raw.values())[0].values()):
            for url in _[1]:
                yield Request(response.urljoin(url), callback=self.parse_recursive)
        # todo get the version title only, feed to chat gpt and get the regex.

        # Recursively follow links
        for link in response.css('a::attr(href)').getall():
            yield Request(response.urljoin(link), callback=self.parse_recursive)

        # Yield the parsed items from this page
        parsed_items = [...]
        yield from parsed_items
