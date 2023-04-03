import re
import logging

def empty_tag_log(tag, tag_name):
    # tag_name = f'tag'.partition('=')[0]+"found"
    if not tag:
        logging.warning("Empty tag called "+tag_name+" has value:" + tag.extract().__str__())

class version:
    platform: None  # str or None
    ver: None  # str
    main_ver: None #int
    sub_ver: None # int
    minor_ver: None #int or 'x'

    def __init__(self, platform, ver):
        self.platform = platform
        self.ver = ver
        self._set_ver()

    def __str__(self):
        return self.platform + ": " + self.ver

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, str):
            other = version(None, other)
            return self==other
        else:
            if self.__hash__()==other.__hash__:
                return True
            if self.platform == other.platform or not self.platform or not other.platform:
                minor_match = self.minor_ver==other.minor_ver or self.minor_ver == 'x' or other.minor_ver=='x'
                if self.main_ver == other.main_ver and self.sub_ver==other.sub_ver and minor_match:
                    return True
            return False

    def __lt__(self, other):
        if isinstance(other, str):
            other = version(None, other)
            return self < other
        else:
            if self == other:
                return False
            if self.platform == other.platform or not self.platform or not other.platform:
                sub_factor = max(self.minor_ver, other.minor_ver)+2
                main_factor = max(self.sub_ver, other.sub_ver)+2
                total_self = self.minor_ver+self.sub_ver*sub_factor+self.main_ver*main_factor*sub_factor
                total_other = other.minor_ver+other.sub_ver*sub_factor+other.main_ver*main_factor*sub_factor
                return total_self < total_other
            raise TypeError("You are comparing two different platform")

    def __le__(self, other):
        if self == other or self < other:
            return True
        else:
            return False

    def __hash__(self):
        return hash((self.platform, self.main_ver, self.sub_ver, self.minor_ver))

    def _set_ver(self):
        splt = self.ver.split('.')
        self.main_ver = int(splt[0])
        self.sub_ver = int(splt[1])
        if len(splt) < 3:
            self.minor_ver = 0
        else:
            self.minor_ver = 'x' if splt[2] == 'x' else int(splt[2])

class mod:
    id: None  # int
    ver: None  # list(version)
    relation_raw: None  # dict(some ver: dict(some relation: list(mod)))
    name_zh: None  # str zh
    name: None  # str
    premod_dict = None  # dict(version: mod)

    def __init__(self, id):
        self.id = id

    @classmethod
    def init_from_href(cls, href):
        r = re.compile(r".*class/(.*)\.html")
        id = r.sub(r"\1", href)
        return cls(id)

    def get_href(self):
        return "https://www.mcmod.cn/class/"+str(self.id)+".html"

    def _get_ver(self, tag, index):
        platform_tag = tag.xpath("./ul[" + str(index) + "]")
        platform = platform_tag.xpath("./li/text()").extract()
        ver = platform_tag.xpath("li/a/text()").extract()
        return (platform, ver)

    def _retrieve_ver(self, response):
        vertag = response.xpath("/html/body/div[2]/div/div[2]/div[2]/div[1]/div[2]/div[2]/div[1]/ul/li/ul")
        self.ver = []
        i = 1
        ver_dict = {}
        while True:
            platform, ver = self._get_ver(vertag, i)
            if platform and ver:
                i += 1
                for v in ver:
                    r = re.compile(r'[a-zA-Z]+')
                    platform_split = r.findall(platform[0])
                    if len(platform_split) > 1:
                        print(platform_split)
                        raise TypeError("Need to check the platform")

                    ver_tmp = version(platform_split[0], v)

                    self.ver.append(ver_tmp)
            else:
                break
        return ver_dict

    def _retrieve_relation(self, response):

        def get_mod_dict(response):
            mod_relation_tag = response.xpath("/html/body/div[2]/div/div[2]/div[2]/div[1]/div[5]/ul/li/ul")
            empty_tag_log(mod_relation_tag, f'mod_relation_tag'.partition('=')[0])
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

        def get_subcollection(tag, index):
            base_pat = "li["+str(index)+"]"
            legend = tag.xpath(base_pat+'/span/text()').extract()
            content = tag.xpath(base_pat+'/ul/li/a/text()').extract()
            href = tag.xpath(base_pat+'/ul/li/a/@href').extract()
            return (legend, content,href)

        def get_table(tag, index):
            ver = tag.xpath("./fieldset["+str(index)+"]/legend/text()").extract()
            sub_tag = tag.xpath("./fieldset["+str(index)+"]")
            if index == 1:
                empty_tag_log(sub_tag, f'sub_tag'.partition('=')[0])
            return (ver, sub_tag)

        mod_dict = get_mod_dict(response)

        self.relation_raw = mod_dict

    def _retrieve_premod(self, platform):

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

        def f_keyword(keyword, dict):
            r = re.compile(keyword)
            keys = list(filter(r.match, dict.keys()))
            return [dict[keys[i]] for i in range(len(keys))]
        self.premod_dict = {}
        mod_dict = self.relation_raw
        premod_dict = get_mod_by_kwd(".*前置", mod_dict)
        premod_forge_dict = get_mod_by_platform('.*'+platform, premod_dict) # dict(ver string: [[mod name], [href string]
        for key,val in premod_forge_dict.items():
            tmpmod = mod.init_from_href(val[1][0])
            r1 = re.compile(r'.*('+platform+'.*)')
            platform_str = r1.sub(r'\1', key)
            r2 = re.compile(r'.*([0-9]{1,2}\.[0-9]{1,2}\.?[0-9x]{1,2}).*')
            ver = r2.sub(r'\1', platform_str)
            tmpversion = version(platform, ver)
            # if not self.ver.index(tmpversion):
            self.premod_dict[tmpversion] = tmpmod

    def extract_info(self, response):
        self._retrieve_ver(response)
        self._retrieve_relation(response)
        self._retrieve_premod('Forge')